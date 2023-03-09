# Fossil Hybrid watches tools and documentation

## Credits

This repo is based on fantastic work done by [Daniel Dakhno](https://github.com/dakhnod) in his [Fossil Hybrid HR SDK](https://github.com/dakhnod/Fossil-HR-SDK). Honestly, none of this work would be possible without reverse engineering done by [Daniel Dakhno](https://github.com/dakhnod). If you find this work useful, pls remember to give a star to the original [Fossil Hybrid HR SDK](https://github.com/dakhnod/Fossil-HR-SDK). You may also find the original repo and tools better than this one.

It is also based on the opensource [Fossil HR Watchface](https://codeberg.org/Freeyourgadget/fossil-hr-watchface) developed by [Arjan Schrijver](https://codeberg.org/arjan5), [Daniel Dakhno](https://codeberg.org/dakhnod), [mvn23](https://codeberg.org/mvn23) and [Morten Hannemose](https://codeberg.org/MortenHannemose) for the [Gadgetbridge project](https://gadgetbridge.org/).

To understand the system better, I encourage you to play with [examples](https://github.com/dakhnod/Fossil-HR-SDK/tree/main/examples) developed by @dakhnod and to read the original [documentation](https://github.com/dakhnod/Fossil-HR-SDK/blob/main/DOCUMENTATION.md) published in the same repo.

## Reason for this fork

I had a couple of reasons to start this work:
- I wanted to improve (imho) tools to be more documented, less error-prone, and easier to be used with Makefile.
- I wanted to start building full, structured documentation for the system.
- I wanted to avoid introducing such massive changes to the original repo as these will introduce incompatibilities with the existing projects. I also hadn't known if the author would like it.
- I didn't want to wait for pull requests to be approved as I started building my watchface and wanted to use these tools immediately.

## Charter for this project

- Build a reliable and well-documented tooling system.
- Build a generic Makefile to build apps.
- Document every known API of the Fossil Hybrid watch system.

# Tools

There are certain tools included in this repository:
| Command | Description |
| --- | --- |
| wapp_image | Encodes/decodes images between PNG and Fossil Hybrid firmware format |
| wapp | Packs/unpacks resources into Fossil Hybrid applications |

Each of the tool provides pretty descriptive help if called with `--help`. You can also find manual with examples of the usage of these apps in the [wiki](../../wiki/wapp.md).

## Installing tools

The recommended way to install tools is to create a separate virtual envirnoment for Python and install tools via pip.

```
# Create and activate virtual envirnoment
$ mkdir Fossil-Tools
$ cd Fossil-Tools
$ python3 -m venv --prompt "Fossil-Tools" .venv
$ . .venv/bin/activate
(Fossil-Tools)$ pip install --upgrade pip
```

```
# Install fossil tools
(Fossil-Tools)$ pip install git+https://github.com/sebo-b/Fossil-Hybrid-Tools.git

# Check if it works
(Fossil-Tools)$ wapp_image
usage: wapp_image [-h] {encode,enc,decode,dec} ...
wapp_image: error: the following arguments are required: {encode,enc,decode,dec}
```

If you want to run any of the tool without venv activation (e.g. from Makefile) you can simply call:
```
{ROOT_PATH}/Fossil-Tools/.venv/bin/wapp_image
```

# Documentation

The documentation is available in [the wiki](../../wiki)

