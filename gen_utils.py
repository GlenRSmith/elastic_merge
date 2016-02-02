#!/usr/bin/env python
#-*- coding:utf-8 -*-
import codecs
import json


def assure_in(a_dict, a_key, a_type):
    if a_key not in a_dict:
        a_dict[a_key] = a_type()
    return a_dict


def read_json_file(filename, as_json=True):
    json_contents = json.loads(
        codecs.open(filename, encoding='UTF8').read())
    if as_json:
        return json_contents
    else:
        return json.dumps(json_contents)
