# linkextr.py - Extract links from Markdown files

Extract links and optionally images from Markdown files. Output sorted list of unique links, one per line.

Extracted links can be further processed by other programs.

Tested on Windows and Linux.

## Install

```bash
git clone https://github.com/wpdevelopment11/linkextr
cd linkextr
python3 -m venv .venv
source .venv/bin/activate

# Install the package which is used to parse Markdown files
pip install mistletoe
```

## Example

Extract links from all Markdown files in the directory (recursively) and output them to stdout:

```bash
./linkextr.py /path/to/dir
```

Same, but output to the file:

```bash
./linkextr.py --output links.txt /path/to/dir
```

Extract links from the specified Markdown files only:

```bash
./linkextr.py first_file.md second_file.md
```

Extract images too, but only if their src starts with `http://` or `https://`:

```bash
./linkextr.py --images first_file.md second_file.md
```

Prefix the links that start with a forward slash to form the valid URL:

```bash
# For example:
# [see this post](/posts/hello-world) => https://example.com/posts/hello-world

./linkextr.py --prefix https://example.com file.md
```

## Usage

```
linkextr.py [-h] [-o OUTPUT] [-p PREFIX] [-a] [-i] [dir | file(s) ...]

Extract links from Markdown files

Positional arguments:
  dir | file(s)        Directory or zero or more Markdown files to extract the links from (default: stdin)

Options:
  -o, --output OUTPUT  File to write extracted links (default: stdout)
  -p, --prefix PREFIX  Add a prefix to the links that start with a forward slash
  -a, --alluri         Extract all links, even if they don't start with http:// or https://
  -i, --images         Extract URLs of images in addition to links
  -h, --help           Show this help message and exit
```

## Run tests

```bash
python3 -m unittest discover test
```

## Limitations

* Only Markdown links are supported, the links from `<a>` HTML tags are not extracted.
