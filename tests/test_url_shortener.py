import unittest
from unittest.mock import patch
from models.pynamodb_model import UrlEntry
from service.url_service import generate_short_url


class TestUrlShortener(unittest.TestCase):

    def test_generate_short_url(self):
        short_url = generate_short_url("https://example.com", None, 6)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 6)
        
    #def test_generate_custom_short_url(self):
        #short_url = generate_short_url("https://example.com", "abcde", 5)
        #self.assertIsNotNone(short_url)
        #self.assertEqual(short_url, "abcde")
        #self.assertEqual(len(short_url), 5)
        
    def test_generate_short_url_with_custom_url(self):
        custom_url = "mycustomurl"
        url = "https://example.com"
        
        with patch("models.pynamodb_model.UrlEntry.get") as mock_get:
            mock_get.return_value = UrlEntry(short_url=custom_url, original_url=url)
            
            with self.assertRaises(ValueError) as context:
                generate_short_url(url, custom_url)
            
            self.assertIn("This custom URL is already in use.", str(context.exception))
