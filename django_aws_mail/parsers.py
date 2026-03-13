import re
from html.parser import HTMLParser as BaseHTMLParser


class HTMLParser(BaseHTMLParser):
    """
    Parser that strips all HTML tags from a string,
    removes the content of the <title> tag,
    and preserves the URLs in <a> tags.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._title = False
        self._href = None
        self._text = []

    def handle_data(self, data):
        if not self._title:
            # collapse whitespace but preserve intentional leading/trailing spaces
            text = re.sub(r'[ \t\r\n]+', ' ', data)
            if text:
                self._text.append(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            # tokenize
            self._text.append('__P__')
        elif tag == 'br':
            # tokenize
            self._text.append('__BR__')
        elif tag in ('div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'ul', 'ol'):
            self._text.append('\n')
        elif tag == 'title':
            self._title = True
        elif tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self._href = attr[1]
                    break

    def handle_endtag(self, tag):
        if tag == 'p':
            self._text.append('__P__')
        elif tag in ('div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'ul', 'ol'):
            self._text.append('\n')
        elif tag == 'title':
            self._title = False
        elif tag == 'a' and self._href:
            self._text.append(f' <{self._href}>')
            self._href = None

    def text(self):
        s = ''.join(self._text)

        # clean up stray spaces around native block newlines
        s = re.sub(r'[ \t]+\n', '\n', s)
        s = re.sub(r'\n[ \t]+', '\n', s)

        # collapse all adjacent block boundary newlines into a single newline
        s = re.sub(r'\n+', '\n', s)

        # restore explicit breaks from our tokens
        s = s.replace('__BR__', '\n')
        s = s.replace('__P__', '\n\n')

        # sweep up again: Remove spaces that got trapped between restored tokens
        s = re.sub(r'[ \t]+\n', '\n', s)
        s = re.sub(r'\n[ \t]+', '\n', s)

        # cap excessive explicit breaks to exactly 2
        s = re.sub(r'\n{3,}', '\n\n', s)

        return s.strip()
