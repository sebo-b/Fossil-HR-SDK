import argparse
from PIL import Image
from math import isqrt
from io import BytesIO
from wapp_tools.utils import ResizeType

def encodeRLE(input, output, resize,**_):

    image = Image.open(input)

    if image.mode != 'RGBA' and image.mode != 'RGB':
        print('image bands have to be RGB or RGBA')
        exit(1)

    width = int(resize[0] or image.width)
    height = int(resize[1] or image.height)

    if width > 0xFF or height > 0xFF:
        print('Image is too big. Maximum resolution is 256x256')
        exit(1)

    if width != image.width or height != image.height:
        print(f"Resize from {image.width}x{image.height} to {width}x{height}")
        image = image.resize((width, height),resample=Image.Resampling.NEAREST)

    outputBuf = bytearray()
    last_pixel = None
    count = 1

    for y in range(0, height):
        for x in range(0, width):

            pixelRGB = image.getpixel((x, y))

            pixel = int((pixelRGB[0] + pixelRGB[1] + pixelRGB[2]) / 3) >> 6

            if len(pixelRGB) > 3:   # RGBA
                alpha = ~(pixelRGB[3]) & 0xc0
                pixel |= (alpha >> 4)

            if last_pixel is None:
                last_pixel = pixel
            elif last_pixel == pixel and count < 255:
                count += 1
            else:
                outputBuf.extend([count,last_pixel])
                last_pixel = pixel
                count = 1

    outputBuf.extend([count,last_pixel])

    output.write(bytes([width,height]))
    output.write(outputBuf)
    output.write(bytes([0xFF,0xFF]))


def encodeRAW(input, output, resize, **_):

    image = Image.open(input)

    if image.mode != 'RGBA' and image.mode != 'RGB':
        print('image bands have to be RGB or RGBA')
        exit(1)

    width = int(resize[0] or image.width)
    height = int(resize[1] or image.height)

    if width != height:
        print('image must be square for raw compression')
        exit(1)

    if width != image.width or height != image.height:
        print(f"Resize from {image.width}x{image.height} to {width}x{height}")
        image = image.resize((width, height),resample=Image.Resampling.NEAREST)

    outputBuf = bytearray()
    shiftCounter = 0
    shiftReg = 0

    for y in reversed(range(0, height)):
        for x in reversed(range(0, width)):

            pixel = image.getpixel((x, y))
            grey = int((pixel[0] + pixel[1] + pixel[2]) / 3) & 0xc0

            shiftReg |= grey >> shiftCounter

            if (shiftCounter == 6):
                outputBuf.append(shiftReg)
                shiftReg = 0
                shiftCounter = 0
            else:
                shiftCounter += 2

    if (shiftCounter != 0):
        outputBuf.append(shiftReg)

    output.write(outputBuf)


# scaling 2 bits to 8 bits, 0 => 0, ... , 0b11 => 0xFF
def bitscale2to8(c):
    return 0x55 * (c & 3)

def decodeRAW(input, output, **_):

    size = 0
    def rawEncoder():
        nonlocal input,size
        while b := input.read(1):     # read is buffered so no optimization is needed
            b = b[0]
            size += 1
            for _a in range(4):
                for _b in range(3):
                    yield bitscale2to8(b >> 6)
                b <<= 2

    pixels = bytes(rawEncoder())

    w = isqrt(size)
    if w*w != size:
        print("Faulty image file - wrong file size")
        exit(1)

    w <<= 1     # 4 pixels per byte, squared

    image = Image.frombuffer('RGB', (w, w), pixels)
    image.transpose(Image.Transpose.ROTATE_180).save(output, 'PNG')

def decodeRLE(input, output, **_):

    try:

        (width,height) = input.read(2)      # can throw ValueError

        image_pixels = bytearray()
        rep = None
        byte = None

        while r := input.read(2):   # read is buffered so no optimization is needed

            if rep is not None:

                color = bitscale2to8(byte)
                alpha = bitscale2to8(~(byte >> 2))
                image_pixels.extend([color, color, color, alpha] * rep)

            (rep, byte) = r     # can throw ValueError

    except ValueError:
        print("Faulty image file - wrong file size")
        exit(1)

    if rep != 0xFF or byte != 0xFF:
        print('Faulty image file, missing 0xFF 0xFF at end')
        exit(1)

    image = Image.frombuffer('RGBA', (width, height), image_pixels)
    image.save(output, 'PNG')

def decode(args):

    if args['format'] == 'auto':

        # I don't want to use seek and tell as we can get streams which are not seekable
        MAX_FILE_SIZE = 4+0xFF*0xFF*2   #256x256x2bytes + 2byte size + 2byte end marker
        buffer = args['input'].read(MAX_FILE_SIZE+1)
        if len(buffer) > MAX_FILE_SIZE:
            print("Format autodetection failed, file is too big.")
            exit(1)

        w = isqrt(len(buffer))
        possibleRAW = (w*w == len(buffer))

        possibleRLE = (len(buffer) % 2 == 0)
        if possibleRLE:
            possibleRLE = buffer[-2:] == b'\xff\xff'
        if possibleRLE:
            numOfPixels = sum(buffer[2:-2:2])
            possibleRLE = (buffer[0]*buffer[1] == numOfPixels)

        if not possibleRAW and not possibleRLE:
            print("Format autodetection failed, unknown file format.")
            exit(1)
        elif possibleRLE and possibleRAW:
            print("RLE format detected, but it may be RAW. Decoding as RLE.")
            args['format'] = 'rle'
        elif possibleRLE:
            print("RLE format detected.")
            args['format'] = 'rle'
        else:
            print("RAW format detected.")
            args['format'] = 'raw'

        args['input'] = BytesIO(buffer)

    if args['format'] == 'rle':
        decodeRLE(**args)
    else:
        decodeRAW(**args)

def encode(args):

    if args['format'] == 'rle':
        encodeRLE(**args)
    else:
        encodeRAW(**args)


def main():

    optParser = argparse.ArgumentParser(description="Encodes/decodes image between PNG and Fossil Hybrid watch format")

    common_options = argparse.ArgumentParser(add_help=False)
    common_options.add_argument(
        "-i","--input",
        required=True,
        metavar="INPUT_FILE",
        type=argparse.FileType('rb'),
        help="Input file (RGBA PNG)")
    common_options.add_argument(
        "-o","--output",
        required=True,
        metavar="OUTPUT_FILE",
        type=argparse.FileType('wb'),
        help="Output file")

    # dest= is needed to handle empty parameter list, see https://bugs.python.org/issue29298
    subparsers = optParser.add_subparsers(title="Commands",required=True, dest="command")

    encode_parser = subparsers.add_parser(
        'encode',
        aliases=['enc'],
        help='Encodes PNG into Fossil image format ',
        parents=[common_options])
    encode_parser.set_defaults(cmd_func=encode)
    encode_parser.add_argument(
        "-s","--resize",
        required=False,
        type=ResizeType(),
        default=(None,None),
        metavar="WIDTHxHEIGHT",
        help="output image size (only WIDTH or xHEIGHT are also allowed)"
        )
    encode_parser.add_argument(
        "-f","--format",
        required=False,
        default="rle",
        choices=['rle','raw'],
        help="Format of the output image, default: rle")

    decode_parser = subparsers.add_parser(
        'decode',
        aliases=['dec'],
        help='Decodes Fossil image format to PNG',
        parents=[common_options])
    decode_parser.set_defaults(cmd_func=decode)
    decode_parser.add_argument(
        "-f","--format",
        required=False,
        default="auto",
        choices=['auto','rle','raw'],
        help="Format of the input image, default autodetect format")

    args = optParser.parse_args()
    args.cmd_func(vars(args))


if __name__ == '__main__':
    main()