import argparse
import os
import json
from wapp_tools import utils
from wapp_tools.wapp_file import WappFile, DIRECTORY

def create_cmd(args):

    try:

        w = WappFile(
            appType = args.app_meta["type"],
            appVersion = args.app_meta["version"],
            displayName = args.app_meta["display_name"])

        if args.verbose:
            print(f"Application type: {args.app_meta['type']}")
            print(f"Application version: {args.app_meta['version']}")
            for k,v in args.app_meta['display_name'].items():
                print(f"{k}: {v}")


        dirs = [
            ('script',DIRECTORY.SCRIPT),
            ('layout',DIRECTORY.LAYOUT),
            ('image',DIRECTORY.IMAGE),
            ('config',DIRECTORY.CONFIG) ]

        for d in dirs:

            files = getattr(args,d[0])
            if files is None:
                continue

            if args.verbose: print(f"\n{d[1].name}:")

            wappDir = w.getDirectory(d[1])
            openParams = {"mode": "r", "encoding": "utf-8"} if wappDir.isTextDir() else {"mode": "rb"}

            for fn in files:

                with open(fn,**openParams) as f:

                    if wappDir.isTextDir():
                        if args.verbose: print("  CHECKING AND MINIFYING JSON")
                        content = json.load(f)
                        content = json.dumps(content)
                    else:
                        content = f.read()

                    bn = os.path.basename(fn)
                    if args.verbose: print(f"  ADD {bn}")
                    wappDir.addFile(bn,content)

        if args.verbose:
            meta = w.getMeta()
            print(f"\nFile content size: {meta['content_size']}")
            print(f"File content crc32: {hex(meta['crc32'])}")

            print("\nWRITING WAPP FILE")

        w.saveToFile(args.output)

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


def extract_cmd(args):

    try:

        w = WappFile(fh = args.input_file)

        try:
            if args.verbose: print(f"       {'DIR'} {args.output}")
            os.mkdir(args.output)
        except FileExistsError:
            print(f"WARNING: directory {args.output} exists.")

        for d in DIRECTORY:

            if d == DIRECTORY.DISPLAY_NAME:
                continue

            dir = w.getDirectory(d)
            if not dir.isEmpty():

                path = os.path.join(args.output,d.name.lower())

                try:
                    if args.verbose: print(f"       {'DIR'} {path}")
                    os.mkdir(path)
                except FileExistsError:
                    print(f"WARNING: directory {args.output} exists.")

                for e in dir:
                    filePath = os.path.join(path,e.file_name)
                    if args.verbose: print(f"{e.file_size:>6} {'TXT' if isinstance(e.content,str) else 'BIN'} {filePath}")
                    with open(filePath,"wb") as file:
                        if isinstance(e.content,str):
                            file.write(e.content.encode('utf-8'))
                        else:
                            file.write(e.content)
        m = w.getMeta()
        appMeta = {
            "version": m["app_version"],
        }

        if m["app_type"] == 1:
            appMeta["type"] = "watchface"
        elif m["app_type"] == 2:
            appMeta["type"] = "application"
        else:
            appMeta["type"] = m["app_type"]

        if "display_name" in m:
            appMeta["display_name"] = m["display_name"]

        appMetaFN = os.path.join(args.output,"app_meta.json")
        with open( appMetaFN,"w", encoding='utf-8') as f:
            if args.verbose: print(f"{'':>6}JSON {appMetaFN}")
            json.dump(appMeta,f,indent=4)

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

def info_cmd(args):

    try:
        w = WappFile(fh = args.input_file)
        print(w)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

def main():

    optParser = argparse.ArgumentParser(description="Create/extract Fossil Hybrid application")

    # dest= is needed to handle empty parameter list, see https://bugs.python.org/issue29298
    subparsers = optParser.add_subparsers(title="Commands",required=True, dest="command")

    create_parser = subparsers.add_parser(
        'create',
        aliases=['c'],
        help='Creates Fossil Hybrid application')
    create_parser.set_defaults(cmd_func=create_cmd)

    create_parser.add_argument(
        "-m","--app_meta",
        required=True,
        type=utils.AppMetaType(),
        metavar="APPMETA_JSON",
        help="Application metadata (json)"
        )
    create_parser.add_argument(
        "-s","--script","--scripts",
        required=True,
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType(),
        metavar="DIR_OR_FILE",
        help="Compiled jerryscript file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-l","--layout","--layouts",
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType(),
        metavar="DIR_OR_FILE",
        help="Layout file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-i","--image","--images",
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType(),
        metavar="DIR_OR_FILE",
        help="Image file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-c","--config","--configs",
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType(),
        metavar="DIR_OR_FILE",
        help="Config file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-o","--output",
        required=True,
        type=argparse.FileType('wb'),
        metavar="OUTPUT_FILE",
        help="Output file (.wapp)"
        )
    create_parser.add_argument(
        "-v","--verbose",
        action='store_true',
        help="Verbose output")

    extract_parser = subparsers.add_parser(
        'extract',
        aliases=['x'],
        help='Extracts resources from Fossil Hybrid application')
    extract_parser.set_defaults(cmd_func=extract_cmd)
    extract_parser.add_argument(
        "-o","--output",
        required=True,
        metavar="OUTPUT_DIR",
        help="Output directory")
    extract_parser.add_argument(
        "-v","--verbose",
        action='store_true',
        help="Verbose output")
    extract_parser.add_argument(
        'input_file',
        type=argparse.FileType('rb'),
        help="Input .wapp file")

    info_parser = subparsers.add_parser(
        'info',
        aliases=['i'],
        help='Prints information about .wapp file')
    info_parser.set_defaults(cmd_func=info_cmd)
    info_parser.add_argument(
        'input_file',
        type=argparse.FileType('rb'),
        help="Input .wapp file")

    args = optParser.parse_args()
    args.cmd_func(args)

if __name__ == '__main__':
    main()