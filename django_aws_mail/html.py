import re
from html.parser import HTMLParser as BaseHTMLParser


class HTMLParser(BaseHTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = re.sub('[ \t\r\n]+', ' ', text)
            self._text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self._text.append('\n\n')
        elif tag == 'br':
            self._text.append('\n')

    def handle_endtag(self, tag):
        if tag == 'p':
            self._text.append('\n\n')

    def text(self):
        return ''.join(self._text).strip()
