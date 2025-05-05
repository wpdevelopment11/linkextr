#!/usr/bin/env python3

from urllib.parse import urlparse

from mistletoe import Document
from mistletoe.base_renderer import BaseRenderer
from mistletoe.span_token import AutoLink, Link, Image
from mistletoe.utils import traverse

import argparse
import glob
import os.path
import sys

def frontmatter_split(lines):
    delimiter = "---"
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or lines[i].rstrip() != delimiter:
        return [], lines
    start = i
    i += 1
    while i < len(lines) and lines[i].rstrip() != delimiter:
        i += 1
    if i >= len(lines):
        return [], lines
    end = i
    return [line.rstrip() + "\n" for line in lines[start:end+1]], lines[end+1:]

def findlinks(lines, prefix=None, images=False, alluri=False):
    links = set()

    if images:
        searchfor = (Link, AutoLink, Image)
    else:
        searchfor = (Link, AutoLink)

    with BaseRenderer():
        doc = Document(lines)
        for result in traverse(doc, searchfor):
            node = result[0]
            if isinstance(node, AutoLink) and node.mailto:
                continue
            uri = node.src if isinstance(node, Image) else node.target

            uri = urlparse(uri)._replace(fragment="")
            if not uri.geturl():
                continue

            if not uri.scheme and uri.netloc:
                uri = uri._replace(scheme="https")
            if prefix and not uri.netloc and uri.path.startswith("/"):
                uri = prefix.rstrip("/") + uri.path
            elif uri.scheme != "mailto" and (uri.netloc or alluri):
                uri = uri.geturl()
            else:
                continue
            links.add(uri)
    return links

def main(args):
    parser = argparse.ArgumentParser(description="Extract links from Markdown files")
    parser.add_argument("path", nargs="*", help="Directory or zero or more Markdown files to extract the links from (default: stdin)", metavar="dir | file(s)")
    parser.add_argument("-o", "--output", help="File to write extracted links (default: stdout)")
    parser.add_argument("-p", "--prefix", help="Add a prefix to the links that start with a forward slash")
    parser.add_argument("-a", "--alluri", action="store_true", help="Extract all links, even if they don't start with http:// or https://")
    parser.add_argument("-i", "--images", action="store_true", help="Extract URLs of images in addition to links")
    args = parser.parse_args(args)

    path, output = args.path, args.output
    del args.path, args.output

    if len(path) == 1 and os.path.isdir(path[0]):
        path = glob.iglob(os.path.join(path[0], "**", "*.md"), recursive=True)

    links = set()
    args = args.__dict__
    if not path:
        lines = sys.stdin.readlines()
        _, lines = frontmatter_split(lines)
        links = findlinks(lines, **args)
    else:
        for file in path:
            with open(file, "r", encoding="utf-8") as md:
                lines = md.readlines()
            _, lines = frontmatter_split(lines)
            links |= findlinks(lines, **args)

    result = [line + "\n" for line in sorted(links)]
    if output:
        with open(output, "w", encoding="utf-8") as out:
            out.writelines(result)
    else:
        sys.stdout.writelines(result)

if __name__ == "__main__":
    main(sys.argv[1:])
