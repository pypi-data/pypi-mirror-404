import unittest

from bdpan.cookies import parse_cookie_text


class TestCookies(unittest.TestCase):
    def test_parse_cookie_header_text(self):
        cookies = parse_cookie_text("a=1; b=2; c=hello%20world")
        self.assertEqual(cookies["a"], "1")
        self.assertEqual(cookies["b"], "2")
        self.assertEqual(cookies["c"], "hello%20world")

    def test_parse_netscape_cookies(self):
        text = """# Netscape HTTP Cookie File
.baidu.com\tTRUE\t/\tFALSE\t0\tBDUSS\tabc
.baidu.com\tTRUE\t/\tFALSE\t0\tSTOKEN\tdef
"""
        cookies = parse_cookie_text(text)
        self.assertEqual(cookies["BDUSS"], "abc")
        self.assertEqual(cookies["STOKEN"], "def")
