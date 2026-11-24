#!/usr/bin/env python3
"""List every star note of the thesis with its page number.

Usage:  python3 tools/notes.py thesis.aux > NOTES.md

Each \\fixnote, \\waiting and \\pendingfigure writes one line
\\thesisnote{page}{text} to thesis.aux when the thesis is built. This
script reads those lines and prints them in the order of the pages, so
the list is always the list of the last build.
"""
import re
import sys


def read_group(s, i):
    """Return (content, index after the closing brace) for the group at s[i] == '{'."""
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == '\\':
            j += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError('unbalanced braces in the .aux file')


def clean(t):
    t = re.sub(r'\\(?:code|nolinkurl|texttt)\s*\{([^{}]*)\}', r'`\1`', t)
    t = re.sub(r'\\[cC]ref\s*\{([^{}]*)\}', r'[\1]', t)
    t = re.sub(r'\\(?:blank|us)\b\s*(?:\{\})?', '', t)
    t = t.replace('\\,', ' ').replace('~', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def label(page):
    return page if page == 'approval page' else 'p. ' + page


def main(path):
    s = open(path, encoding='utf-8', errors='replace').read()
    notes = []
    for m in re.finditer(r'\\thesisnote\s*\{', s):
        page, i = read_group(s, m.end() - 1)
        text, _ = read_group(s, i)
        page, text = page.strip(), clean(text)
        if re.fullmatch(r'\[[^\]]+\]', text):
            # a bracketed item on the committee approval page, which carries no page number
            page, text = 'approval page', 'fill in ' + text
        notes.append((page, text))
    waiting = [n for n in notes if n[1].startswith('Waiting for')]
    other = [n for n in notes if not n[1].startswith('Waiting for')]
    print('# Star notes in the thesis')
    print()
    print('Every note below is printed in the PDF with a star (*) in front of it. '
          'Nothing else in the PDF uses that character, so a search for * finds all of them. '
          'Page numbers are those printed on the pages of the last build '
          '(roman numbers are the front matter).')
    print()
    print('%d notes: %d wait for a result or a record, %d are things to fix, confirm or write.'
          % (len(notes), len(waiting), len(other)))
    print()
    print('## Waiting for results')
    print()
    for page, text in waiting:
        print('- %s: %s' % (label(page), text))
    print()
    print('## To fix, confirm or write')
    print()
    for page, text in other:
        print('- %s: %s' % (label(page), text))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'thesis.aux')
