import unittest
from unittest.mock import patch
from models.pynamodb_model import UrlEntry
from models.url_pydantic_models import URLRequest
from service.url_service import *
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app

client = TestClient(app)

class TestUrlShortener(unittest.TestCase):

    def test_generate_short_url(self):
        short_url = generate_short_url("https://example.com", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
    
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    def test_generate_short_url_no_collision(self, mock_save, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist
        mock_save.return_value = None
        
        short_url = generate_short_url("https://example.com", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
        
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    def test_generate_short_url_with_collision(self, mock_save, mock_get):
        #simulate collision with first short url
        mock_get.side_effect = [UrlEntry(short_url="unique_url", original_url="https://example.com"), UrlEntry.DoesNotExist]
        mock_save.return_value = None
        
        short_url = generate_short_url("https://example.com", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
        self.assertNotEqual(short_url, "unique_url")
        
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
        
        #test invalid url format
    def test_generate_short_url_malformed(self):
        with self.assertRaises(ValueError) as context:
            generate_short_url("example.com")
        self.assertIn("Invalid URL format", str(context.exception))
        
        #test get og url for nonexistent short url
    @patch("models.pynamodb_model.UrlEntry.get")  
    def test_get_original_url_nonexistent_short_url(self, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist
        with self.assertRaises(ValueError) as context:
            get_original_url("nonexistent")
        self.assertIn("Short URL does not exist.", str(context.exception))
        
        #test invalid url length
    def test_generate_short_url_invalid_length(self):
        with self.assertRaises(ValidationError) as context:
            URLRequest(url= "https://example.com", length=6)
        self.assertEqual(context.exception.errors()[0]["msg"], "Input should be greater than or equal to 10")
        
       #test invalid custom url length
    def test_generate_short_url_invalid_custom_str_length(self):
        with self.assertRaises(ValidationError) as context:
            URLRequest(url= "https://example.com", custom_url = "short")
        self.assertEqual(context.exception.errors()[0]["msg"], "String should have at least 10 characters")    
        
        
    @patch("models.pynamodb_model.UrlEntry.scan")
    def test_list_urls(self, mock_scan):
        mock_scan.return_value = [UrlEntry(short_url="short1", original_url="https://example1.com"),
                                  UrlEntry(short_url="short2", original_url="https://example2.com")]
        
        expected_result = {"short1": "https://example1.com",
                           "short2": "https://example2.com"}
        
        result = get_url_list()
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected_result)
        
    
  
    