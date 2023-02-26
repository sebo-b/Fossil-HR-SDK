import argparse
import utils

def create_cmd(args):

    print(args)
    pass

def extract_cmd(args):

    print("NOT IMPLEMENTED")
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
        'encode',
        aliases=['c'],
        help='Creates Fossil Hybrid application')
    create_parser.set_defaults(cmd_func=create_cmd)

    create_parser.add_argument(
        "-m","--app_meta",
#        required=True,
        type=utils.AppMetaType(),
        metavar="APP_JSON",
        help="Application metadata (json)"
        )
    create_parser.add_argument(
        "-s","--script","--scripts",
#        required=True,
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType('rb'),
        metavar="DIR_OR_FILE",
        help="Compiled jerryscript file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-l","--layout","--layouts",
#        required=True,
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType('rb'),
        metavar="DIR_OR_FILE",
        help="Layout file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-i","--image","--images",
#        required=True,
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType('rb'),
        metavar="DIR_OR_FILE",
        help="Image file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-c","--config","--configs",
#        required=True,
        action=utils.FlatExtendAction,
        nargs='+',
        type=utils.DirOrFileType('r'),
        metavar="DIR_OR_FILE",
        help="Config file or dir containing files. This option can be specified multiple times."
        )
    create_parser.add_argument(
        "-o","--output",
#        required=True,
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

    args = optParser.parse_args()
    args.cmd_func(vars(args))

if __name__ == '__main__':
    main()