import unittest
from unittest.mock import patch, MagicMock
from models.pynamodb_model import UrlEntry
from service.url_service import *
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

class TestUrlShortener(unittest.TestCase):

    def test_generate_short_url(self):
        short_url = generate_short_url("https://example.com", None, 6)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 6)
    
    @patch("models.pynamodb_model.UrlEntry.save")
    def test_generate_short_url_no_collision(self, mock_save):
        short_url = generate_short_url("https://example.com", None, 6)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 6)
        
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    def test_generate_short_url_with_collision(self, mock_save, mock_get):
        mock_get.side_effect = [UrlEntry(short_url="unique", original_url="https://example.com"), UrlEntry.DoesNotExist]
        mock_save.return_value = None
        
        short_url = generate_short_url("https://example.com", None, 6)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 6)
        self.assertNotEqual(short_url, "unique")
        
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")    
    def test_generate_custom_url_no_collision(self, mock_save, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist
        mock_save.return_value = None
        
        custom_url = "mycustomurl"             
        short_url = generate_short_url("https://example.com", custom_url)
        self.assertIsNotNone(short_url)            
        self.assertEqual(short_url, custom_url)
    
    @patch("models.pynamodb_model.UrlEntry.get")        
    def test_generate_custom_url_with_collision(self, mock_get):
        mock_get.return_value = UrlEntry(short_url="mycustomurl", original_url="https://example.com")
              
        with self.assertRaises(ValueError) as context:
            generate_short_url("https://example.com", "mycustomurl")            
        self.assertIn("This custom URL is already in use.", str(context.exception))
        
    @patch("models.pynamodb_model.UrlEntry.scan")
    def test_list_urls(self, mock_scan):
        mock_scan.return_value = [UrlEntry(short_url="short1", original_url="https://example1.com"),
                                  UrlEntry(short_url="short2", original_url="https://example2.com")]
        
        expected_result = {"short1": "https://example1.com",
                           "short2": "https://example2.com"}
        
        result = get_url_list()
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected_result)
        
    
  
    