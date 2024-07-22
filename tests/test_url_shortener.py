import unittest
from service.url_service import generate_short_url


class TestUrlShortener(unittest.TestCase):

    def test_generate_short_url(self):
        short_url = generate_short_url("https://example.com", 6)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 6)
