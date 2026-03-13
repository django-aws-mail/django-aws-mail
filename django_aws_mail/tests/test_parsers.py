from django.test import TestCase
from django_aws_mail.parsers import HTMLParser


class HTMLParserTests(TestCase):

    def parse_html(self, html_content):
        """Helper to feed HTML and return the parsed text."""
        parser = HTMLParser()
        parser.feed(html_content)
        parser.close()
        return parser.text()

    def test_strip_basic_tags(self):
        """Test that standard HTML tags are removed but content is kept."""
        html = "<html><body><h1>Heading</h1><div>Some text</div></body></html>"
        text = self.parse_html(html)
        self.assertEqual(text, "Heading\nSome text")

    def test_ignore_title_tag(self):
        """Test that the <title> tag and its content are completely ignored."""
        html = "<head><title>Ignore Me</title></head><body>Keep Me</body>"
        text = self.parse_html(html)
        self.assertEqual(text, "Keep Me")

    def test_paragraph_and_br_formatting(self):
        """Test that <p> and <br> tags introduce the correct line breaks."""
        html = "<p>First paragraph.</p><p>Second paragraph.<br>Next line.</p>"
        text = self.parse_html(html)

        expected_text = "First paragraph.\n\nSecond paragraph.\nNext line."
        self.assertEqual(text, expected_text)

    def test_anchor_tag_urls_preserved(self):
        """Test that href attributes from <a> tags are appended after the text."""
        html = 'Visit our <a href="https://example.com">website</a> for more info.'
        text = self.parse_html(html)

        # Should append the URL in brackets after the anchor text
        self.assertEqual(text, "Visit our website <https://example.com> for more info.")

    def test_whitespace_reduction(self):
        """Test that excessive spaces and newlines are normalized."""
        html = "<p>This    has   way   too   much   space.</p>\n\n\n<p>And lots of blank lines.</p>"
        text = self.parse_html(html)

        expected_text = "This has way too much space.\n\nAnd lots of blank lines."
        self.assertEqual(text, expected_text)

    def test_inline_vs_block_tags(self):
        """Test that inline tags flow naturally while block tags create line breaks."""
        html = "<div>Block 1</div><span>Inline 1 </span><strong>Inline 2</strong><h2>Block 2</h2><ul><li>Item 1</li><li>Item 2</li></ul>"
        text = self.parse_html(html)

        # Spans and strongs should stay on the same line, while lists and headings break.
        expected_text = "Block 1\nInline 1 Inline 2\nBlock 2\nItem 1\nItem 2"
        self.assertEqual(text, expected_text)

    def test_anchor_bracket_edge_case(self):
        """Test the specific edge case with brackets around anchor tags."""
        html = 'Please click [<a href="https://example.com">here</a>].'
        text = self.parse_html(html)

        # Because we preserved natural spaces, the brackets shouldn't have weird padding inside them!
        self.assertEqual(text, "Please click [here <https://example.com>].")

    def test_excessive_newlines_collapsed(self):
        """Test that 3 or more newlines are safely collapsed into a standard paragraph break."""
        # This simulates a user putting way too many <br> tags or empty <p> tags
        html = "<p>First</p><br><br><br><br><p>Second</p>"
        text = self.parse_html(html)

        # It should cap out at exactly 2 newlines (one empty line between text)
        self.assertEqual(text, "First\n\nSecond")
