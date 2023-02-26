
import argparse
import json
import os
import re
from jsonschema import validate, ValidationError

class ResizeType(object):

    def __call__(self,s):
        m = re.match('([0-9]+)?(?:x([0-9]+))?$',s)
        if m is None:
             raise argparse.ArgumentTypeError("invalid value")
        return m.groups()


class AppMetaType(object):

    schemaFile = "appmeta_schema.json"

    def __init__(self):
        with open(self.schemaFile) as schema:
            self.schema = json.load(schema)


    def __call__(self,s):

        appmeta = {}

        try:
            with open(s,"r") as meta_f:
                appmeta = json.load(meta_f)
        except json.JSONDecodeError:
            raise argparse.ArgumentTypeError("not a valid JSON file")

        try:
            validate(appmeta,self.schema)
        except ValidationError as jsonerr:
            if len(jsonerr.relative_path) == 1 and jsonerr.relative_path[0] == "version":
                raise argparse.ArgumentTypeError(f"format of version must be x.y.z")
            raise argparse.ArgumentTypeError(f"invalid json format: {jsonerr.message}")

        if not isinstance(appmeta['type'],int):
            appmeta['type'] = {
                "face": 1,
                "watchface": 1,
                "app": 2,
                "application": 2,
                }[appmeta['type']]

        return appmeta

class DirOrFileType(object):

    def __init__(self, mode='r', encoding="utf-8"):

        encoding = None if 'b' in mode else encoding
        self.ft = argparse.FileType(mode, encoding = encoding)

    def __call__(self,param):

        if isinstance(param,str):
            param = [param]

        files = []
        for p in param:
            if os.path.isdir(p):
                files.extend(os.listdir(p))
            else:
                files.append(p)

        fileTypes = [self.ft(f) for f in files]

        return fileTypes

def _deepIter(values):
    if not (isinstance(values,list) or isinstance(values,tuple)):
        yield values
    else:
        for i in values:
            yield from _deepIter(i)


class FlatExtendAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        items.extend(_deepIter(values))
        setattr(namespace, self.dest, items)
