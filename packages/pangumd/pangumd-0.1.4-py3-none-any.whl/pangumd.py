import argparse
import os
import sys
import unicodedata
from contextlib import contextmanager

import pangu
from marko import Markdown
from marko.md_renderer import MarkdownRenderer

__version__ = '0.1.4'
__all__ = ['spacing', 'spacing_file', 'cli']


class SpacingMarkdownRenderer(MarkdownRenderer):
    def __init__(self):
        super().__init__()
        self._last_char = None
        self._prefix_spaces = []
        self._add_prefix_to_raw = True
        self._spacing = True

    @contextmanager
    def no_prefix_for_raw(self):
        self._add_prefix_to_raw = False
        yield
        self._add_prefix_to_raw = True

    @contextmanager
    def no_spacing_for_raw(self):
        self._spacing = False
        yield
        self._spacing = True

    def render_raw_text(self, element):
        if (not element.children) or (not self._spacing):
            return element.children

        text = pangu.spacing(element.children)
        prefix = self.get_prefix_space(element.children[0])

        if self._add_prefix_to_raw:
            text = prefix + text
        else:
            self._prefix_spaces.append(prefix)

        self._last_char = text[-1] if text else None
        return text

    def render_code_span(self, element):
        text = element.children
        if text:
            prefix = self.get_prefix_space(text[0])
            self._last_char = text[-1]
        else:
            prefix = ''
            self._last_char = None
        return prefix + super().render_code_span(element)

    def render_strong_emphasis(self, element):
        return self.set_prefix(super().render_strong_emphasis, element)

    def render_emphasis(self, element):
        return self.set_prefix(super().render_emphasis, element)

    def set_prefix(self, method, element):
        with self.no_prefix_for_raw():
            text = method(element)
        return self._prefix_spaces.pop() + text

    def get_prefix_space(self, char):
        empty = ''

        if not self._last_char or self._last_char.isspace():
            return empty

        c = unicodedata.category(char)
        if c.startswith('P'):
            return empty

        last_c = unicodedata.category(self._last_char)
        if last_c.startswith('P'):
            return empty

        if last_c == c:
            return empty

        return ' '

    def render_line_break(self, element):
        self._reset_last()
        return super().render_line_break(element)

    def render_blank_line(self, element):
        self._reset_last()
        return super().render_blank_line(element)

    def render_list_item(self, element):
        self._reset_last()
        return super().render_list_item(element)
    
    def render_fenced_code(self, element):
        with self.no_spacing_for_raw():
            return super().render_fenced_code(element)

    def _reset_last(self):
        self._last_char = None


def spacing(text):
    md_to_md = Markdown(renderer=SpacingMarkdownRenderer)
    return md_to_md(text)


def spacing_text(text):
    return spacing(text).rstrip()


def spacing_file(path):
    """
    Perform paranoid text spacing on file content.
    Automatically detects markdown files and uses mistletoe parser if available.

    Args:
        path: The file path to read and process

    Returns:
        The processed file content with proper spacing
    """
    with open(os.path.abspath(path), encoding='utf-8') as f:
        content = f.read()
        return spacing_text(content)


def cli():
    parser = argparse.ArgumentParser(
        prog='pangumd',
        description=(
            'Paranoid text spacing for good readability, to automatically '
            'insert whitespace between CJK and half-width characters '
            '(alphabetical letters, numerical digits and symbols).'
        ),
    )
    parser.add_argument('-v', '--version', action='version', version=__version__)
    parser.add_argument(
        '-t',
        '--text',
        action='store_true',
        dest='is_text',
        required=False,
        help='specify the input value is a text',
    )
    parser.add_argument(
        '-f',
        '--file',
        action='store_true',
        dest='is_file',
        required=False,
        help='specify the input value is a file path',
    )
    parser.add_argument(
        'text_or_path', action='store', type=str, help='the text or file path to apply spacing'
    )

    if not sys.stdin.isatty():
        print(spacing_text(sys.stdin.read()))
    else:
        args = parser.parse_args()
        if args.is_text:
            print(spacing_text(args.text_or_path))
        elif args.is_file:
            print(spacing_file(args.text_or_path))
        else:
            print(spacing_text(args.text_or_path))


def format():
    parser = argparse.ArgumentParser(
        description=(
            'Paranoid text spacing for good readability, to automatically '
            'insert whitespace between CJK (Chinese, Japanese, Korean) and '
            'half-width characters (alphabetical letters, numerical digits '
            'and symbols).'
        )
    )
    parser.add_argument('files', nargs='+', help='Files to be processed')
    args = parser.parse_args()

    for filepath in args.files:
        content = spacing_file(filepath)
        with open(filepath, 'w') as f:
            f.write(content)


if __name__ == '__main__':
    cli()
