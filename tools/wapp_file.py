
from enum import IntEnum
from struct import unpack_from, pack_into, pack
from crc32c import crc32c

class _OFFSET(IntEnum):
    MAGIC = 0x00
    FILE_VERSION = 0x02
    UNKN_ZEROS_1 = 0x04
    CONTENT_SIZE = 0x08
    CONTENT = 0x0c
    APP_TYPE = 0x0c
    APP_VERSION = 0x0d
    UNKN_ZEROS_2 = 0x10
    SCRIPT_DIR = 0x18
    IMAGES_DIR = 0x1c
    LAYOUT_DIR = 0x20
    UNKN1_DIR = 0x24
    DISPLAY_NAME_DIR = 0x28
    CONFIG_DIR = 0x2c
    UNKN2_DIR = 0x30
    APP_INFO_DIR = 0x34
    UNKN_ZEROS_3 = 0x38
    HEADER_SIZE = 0x58

class DIRECTORY(IntEnum):
    SCRIPT = _OFFSET.SCRIPT_DIR
    IMAGE = _OFFSET.IMAGES_DIR
    LAYOUT = _OFFSET.LAYOUT_DIR
    UNKN1 = _OFFSET.UNKN1_DIR
    DISPLAY_NAME = _OFFSET.DISPLAY_NAME_DIR
    CONFIG = _OFFSET.CONFIG_DIR
    UNKN2 = _OFFSET.UNKN2_DIR
    APP_INFO = _OFFSET.APP_INFO_DIR

_TEXT_DIRS = [DIRECTORY.LAYOUT, DIRECTORY.DISPLAY_NAME, DIRECTORY.CONFIG]

class WappDirEntry:

    def __init__(self,file_name,file_size,content):
        self.file_name = file_name
        self.file_size = file_size
        self.content = content

    def __str__(self):
        return f"{self.file_size:>5} {self.file_name}"


class WappDirectory:

    def __init__(self, wappFile, directoryBuf,textDir):

        self.wappFile = wappFile
        self.directoryBuf = directoryBuf
        self.textDir = textDir

    def __iter__(self):

        i = 0
        dirView = memoryview(self.directoryBuf)     #memoryview also prevents resize of underlying buffer
        while i < len(dirView):

            offset = i

            fnLen = unpack_from('<B',dirView,i)[0]
            i += 1

            fn = str(dirView[i:i+fnLen-1],'utf-8')    # skipping null-terminator
            i += fnLen

            fileSize = unpack_from('<H',dirView,i)[0]
            i += 2

            content = dirView[i:i+fileSize]
            if self.textDir:
                content = str(content[:-1],'utf-8') #skipping null-terminator

            i += fileSize

            yield WappDirEntry(fn,fileSize,content)

    def __str__(self):

        ret = ""
        for e in self:
            ret += " "+str(e)+"\n"

        return ret

    def isEmpty(self):
        return len(self.directoryBuf) == 0

    def isTextDir(self):
        return self.textDir

    def clean(self):

        if self.isEmpty():
            return

        self.wappFile.dirty = True
        self.directoryBuf.clear()


    def addFile(self,fileName,content):

        self.wappFile.dirty = True

        fileNameBin = bytearray(fileName.encode('utf-8'))
        if len(fileNameBin) > 0xFE:     # 0xff - null terminator
            print("WARNING: file name too long, trimming to 254 bytes: {bn}")
            cutPoint = 0xFE
            if fileNameBin[cutPoint] & 0xc0 == 0x80:    # mid of utf-8 seq
                while fileNameBin[cutPoint] & 0xc0 == 0x80:
                    cutPoint -= 1
            fileNameBin = fileNameBin[:cutPoint]
        fileNameBin.append(0)   # null terminator

        fileBuf = bytearray()
        fileBuf.extend(pack('<B',len(fileNameBin)))
        fileBuf.extend(fileNameBin)

        if isinstance(content,str):
            content = content.encode('utf-8')

        contentSize = len(content)
        if self.textDir:
            contentSize += 1

        fileBuf.extend(pack('<H',contentSize))
        fileBuf.extend(content)

        if self.textDir:
            fileBuf.extend(b'\x00')

        self.directoryBuf.extend(fileBuf)


class WappFileError(Exception):
    pass

class WappFile:


    def __init__(self,fh = None, appType = None, appVersion = None, displayName = None):

        self.dirty = True

        if fh is not None:
            self._parse(fh)
        elif appType is not None and appVersion is not None:
            self._createEmpty(appType,appVersion,displayName)
        else:
            raise ValueError("Either file handle or appType and appVersion must be provided")

        self.dirty = False

    def _parse(self,fh):

        wappFile = bytearray(fh.read())

        magic = unpack_from('<H',wappFile,_OFFSET.MAGIC)[0]
        if magic != 0x15FE:
            raise WappFileError("Wrong file, magic check failed.")

        fileSize = unpack_from('<I',wappFile,_OFFSET.CONTENT_SIZE)[0]
        if fileSize + _OFFSET.CONTENT + 4 != len(wappFile): # +4 is CRC32 size
            raise WappFileError("Wrong file, file size check failed.")

        self.crc32 = unpack_from('<I',wappFile,len(wappFile)-4)[0]
        calculatedCRC = crc32c(memoryview(wappFile)[_OFFSET.CONTENT:-4])

        if self.crc32 != calculatedCRC:
            raise WappFileError("Wrong file, checksum failed.")

        fileVersion = unpack_from('<H',wappFile,_OFFSET.FILE_VERSION)[0]
        if fileVersion != 3:
            print(f"WARNING: File version is {fileVersion} while version 3 is supported. It may be wrongly parsed.")

        self.header = wappFile[0:_OFFSET.HEADER_SIZE]
        self.directories = {}

        offsets = [*unpack_from("<IIIIIIII",self.header,_OFFSET.SCRIPT_DIR),len(wappFile)-4]    # file end as the last offset

        #fix (possible) zeros
        for i in range(len(offsets)):
            if offsets[i] == 0:
                if i == 0:
                    raise ValueError("SCRIPT has offset 0")
                offsets[i] = offsets[i-1]

        for i,dir in enumerate(DIRECTORY):

            if offsets[i+1] - offsets[i] == 0:
                self.directories[dir] = bytearray()
            else:
                self.directories[dir] = wappFile[offsets[i]:offsets[i+1]]

        self._updateMeta()


    def _createEmpty(self,appType,appVersion,displayName):

        self.header = bytearray(_OFFSET.HEADER_SIZE)
        self.directories = {}
        for d in DIRECTORY:
            self.directories[d] = bytearray()

        pack_into('<H',self.header,_OFFSET.MAGIC,0x15FE)
        pack_into('<H',self.header,_OFFSET.FILE_VERSION,3)
        pack_into('B',self.header,_OFFSET.APP_TYPE,appType)

        ver = tuple(int(i) & 0xFF for i in appVersion.split('.'))
        pack_into('BBB',self.header,_OFFSET.APP_VERSION,*ver)

        if displayName is not None:
            dir = self.getDirectory(DIRECTORY.DISPLAY_NAME)

            for item in displayName.items():
                dir.addFile(*item)

        self._updateMeta()


    def _updateMeta(self):

        if not self.dirty:
            return

        fileSize = 0

        lastOffset = 0
        lastSize = len(self.header)
        for id in DIRECTORY:
            pack_into('<I',self.header,id,lastOffset+lastSize)
            lastOffset += lastSize
            lastSize = len(self.directories[id])

        contentSize = lastOffset + lastSize - _OFFSET.CONTENT
        pack_into("<I",self.header,_OFFSET.CONTENT_SIZE,contentSize)

        crc32 = crc32c(memoryview(self.header)[_OFFSET.CONTENT:])
        for id in DIRECTORY:
            crc32 = crc32c(self.directories[id],crc32)

        self.crc32 = crc32


    def __str__(self):

        meta = self.getMeta()
        type = "watchface" if meta['app_type'] == 1 else "application"
        type += f" ({meta['app_type']})"

        retStr = \
            f"File version: {meta['file_version']}\n" \
            f"File content size: {meta['content_size']}\n" \
            f"File content crc32: {hex(meta['crc32'])}\n" \
            f"Application type: {type}\n" \
            f"Application version: {meta['app_version']}\n"

        if "display_name" in meta and "display_name" in meta["display_name"]:
            retStr += f"Display name: {meta['display_name']['display_name']}\n"

        for d in DIRECTORY:
            dir = self.getDirectory(d)
            if dir.isEmpty():
                continue
            retStr += f"\n{d.name}:\n{dir}"

        return retStr

    def getMeta(self):

        self._updateMeta()

        ret = {
            "file_version": unpack_from("<H",self.header,_OFFSET.FILE_VERSION)[0],
            "content_size": unpack_from("<I",self.header,_OFFSET.CONTENT_SIZE)[0],
            "app_type": unpack_from("B",self.header,_OFFSET.APP_TYPE)[0],
            "app_version": "{0}.{1}.{2}".format( *unpack_from("BBB",self.header,_OFFSET.APP_VERSION)),
            "crc32": self.crc32
        }

        ret["display_name"] = {}
        for f in self.getDirectory(DIRECTORY.DISPLAY_NAME):
            ret["display_name"][f.file_name] = f.content
        if not ret["display_name"]:
            del ret["display_name"]

        return ret


    def getDirectory(self,dir):

        if not dir in self.directories:
            raise KeyError

        return WappDirectory(self,self.directories[dir],dir in _TEXT_DIRS)

    def saveToFile(self,fh):

        self._updateMeta()

        fh.write(self.header)
        for d in DIRECTORY:
            fh.write(self.directories[d])
        fh.write(pack('<I',self.crc32))


