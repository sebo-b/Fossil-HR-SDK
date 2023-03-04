import argparse
import os
import json
from wapp_tools import utils
from wapp_tools.wapp_file import WappFile, DIRECTORY

def create_cmd(args):

    print(args)
    print("NOT IMPLEMENTED")
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

#    create / c
#      --app_meta / -m (check with json schema)
#           face/app: bool
#           version: x.y.z
#           display_name: string
#           theme_class: string, optional
#      --script / --scripts / -s  dir/ or jerry script file, multiple times (check if jerry)
#      --layout / --layouts / -l dir/or layout file, multiple times (minify)
#      --image / --images / -i dir/or image file, multiple times (check if image)
#      --config / --configs / -c dir/or config file (minify)
#      -o output_file
#    extract / x
#      -o output directory (creates if doesn't exist)

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