# Copyright (c) 2001 Chris Withers
#
# This Software is released under the MIT License:
# http://www.opensource.org/licenses/mit-license.html
# See license.txt for more details.
#
# The original version of this file comes from stripogram

"""
HTML to text parser.

"""

import HTMLParser

import re, htmlentitydefs

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)




class HTML2Text(HTMLParser.HTMLParser):
    """Html parser outputting raw text, more or less formatted"""
    def __init__(self, ignore_tags=(), indent_width=4, page_width=80):
        HTMLParser.HTMLParser.__init__(self)
        self.result = ''
        self.indent = 0
        self.ol_number = 0
        self.td_number = 0
        self.page_width = page_width
        self.inde_width = indent_width
        self.lines = []
        self.line = []
        self.ignore_tags = ignore_tags

    def add_text(self, text):
        """Add words to the current line."""

        words = unescape(text).replace('\n', ' ').split()
        self.line.extend(words)

    def add_break(self):
        """End the current line."""
        self.lines.append((self.indent, self.line))
        self.line = []

    def generate(self):
        """Output the generated text, formatting it correctly."""
        # Join lines with indents
        indent_width = self.inde_width
        page_width = self.page_width
        out_paras = []

        for indent, line in self.lines + [(self.indent, self.line)]:
            i = indent * indent_width
            indent_string = i * ' '
            line_width = page_width - i
            out_para = ''
            out_line = []
            len_out_line = 0

            for word in line:
                len_word = len(word)
                if len_out_line + len_word < line_width:
                    out_line.append(word)
                    len_out_line = len_out_line + len_word
                else:
                    out_para += indent_string + ' '.join(out_line) + '\n'
                    out_line = [word]
                    len_out_line = len_word
            
            out_para += indent_string + ' '.join(out_line)
            out_paras.append(out_para)
            
        self.result = '\n\n'.join(out_paras)

    def mod_indent(self, i):
        """Modify the current indentation level"""
        self.indent += i
        if self.indent < 0:
            self.indent = 0
        
    def handle_data(self, data):
        """Add text from html data"""
        if data:
            self.add_text(data)

    def handle_starttag(self, tag, attrs):
        """Handles unknown tags"""
        tag = tag.lower()
        
        if tag not in self.ignore_tags:
            if tag[0] == 'h' or tag in ('br', 'pre', 'p'):
                self.add_break()
            elif tag == 'img':
                src = ''
                for key, value in attrs:
                    if key.lower() == 'src':
                        src = value
                self.add_break()
                self.add_text('Image: ' + src)
            elif tag == 'li':
                self.add_break()
                if self.ol_number:
                    self.add_text(str(self.ol_number) + ' - ')
                    self.ol_number += 1
                else:
                    self.add_text('- ')
            elif tag == 'dt':
                self.add_break()
                self.mod_indent(-1)
            elif tag == 'dd':
                self.add_break()
                self.mod_indent(+1)
            elif tag == 'ol':
                self.ol_number = 1
            elif tag == 'table':
                self.add_break()
                
    def handle_endtag(self, tag):
        """Handle unknowns tags"""
        tag = tag.lower()
        
        if tag not in self.ignore_tags:
            if tag[0] == 'h' or tag == 'pre':
                self.add_break()
            elif tag == 'dl':
                self.add_break()
                self.mod_indent(-1)
            elif tag in ('ul', 'ol'):
                self.add_break()
                self.ol_number = 0
            elif tag in ('table', 'tr'):
                self.add_break()
                self.mod_indent(- self.td_number)
                self.td_number = 0
            elif tag == 'td':
                self.td_number += 1
                self.add_text(' | ')
                self.mod_indent(+1)


def html2text(string, ignore_tags=(), indent_width=4, page_width=80):
    """Function wrapping the class functionality."""
    string = unescape(string)
    parser = HTML2Text(ignore_tags, indent_width, page_width)
    parser.feed(string)
    parser.close()
    parser.generate()
    return parser.result
