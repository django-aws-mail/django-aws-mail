import re
from html.parser import HTMLParser as BaseHTMLParser


class HTMLParser(BaseHTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._href = None
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
        elif tag == 'a':
            # attrs is a list of tuples: [('href', 'link'), ...]
            for attr in attrs:
                if attr[0] == 'href':
                    self._href = attr[1]
                    break

    def handle_endtag(self, tag):
        if tag == 'p':
            self._text.append('\n\n')
        elif tag == 'a' and self._href:
            # add the url that was found in starttag
            self._text.append(f'<{self._href}>')
            self._href = None

    def text(self):
        s = ''.join(self._text)

        # remove excessive white-space
        s = s.strip()
        s = re.sub(r'( {2,})', '', s)
        s = re.sub(r'(\s{3,})', '\n\n', s)
        return s
