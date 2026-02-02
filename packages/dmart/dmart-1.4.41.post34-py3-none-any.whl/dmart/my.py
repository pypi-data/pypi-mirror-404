#!/usr/bin/python3
#coding: utf-8

from pygments import highlight, lexers, formatters
import json

d = {"test": [1, 2, 3, 4], "hello": "world"}

formatted_json = json.dumps(d, indent=4)
colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
print(colorful_json)
