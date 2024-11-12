import unittest
from unittest.mock import patch
from models.pynamodb_model import UrlEntry
from models.url_pydantic_models import URLRequest, UserRequest
from service.url_service import *
from service.exceptions import *
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import app

client = TestClient(app)

class TestUrlShortener(unittest.TestCase):

    @patch("models.pynamodb_model.UserEntry.get") 
    def test_generate_short_url(self, mock_user):
        mock_user.return_value = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")  
        short_url = generate_short_url("https://example.com", "test_user", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
    
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    @patch("models.pynamodb_model.UserEntry.get") 
    def test_generate_short_url_no_collision(self, mock_user, mock_save, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist
        mock_save.return_value = None
        mock_user.return_value = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")  
        
        short_url = generate_short_url("https://example.com", "test_user", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
        
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    @patch("models.pynamodb_model.UserEntry.get") 
    def test_generate_short_url_with_collision(self, mock_user, mock_save, mock_get):
        #simulate collision with first short url
        mock_get.side_effect = [UrlEntry(short_url="unique_url", original_url="https://example.com"), UrlEntry.DoesNotExist]
        mock_save.return_value = None
        mock_user.return_value = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")  
        
        short_url = generate_short_url("https://example.com", "test_user", None, 10)
        self.assertIsNotNone(short_url)
        self.assertEqual(len(short_url), 10)
        self.assertNotEqual(short_url, "unique_url")
        
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save") 
    @patch("models.pynamodb_model.UserEntry.get")   
    def test_generate_custom_url_no_collision(self,mock_user, mock_save, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist
        mock_save.return_value = None
        mock_user.return_value = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")  
        
        custom_url = "mycustomurl"             
        short_url = generate_short_url("https://example.com", "test_user", custom_url)
        self.assertIsNotNone(short_url)            
        self.assertEqual(short_url, custom_url)
    
    @patch("models.pynamodb_model.UrlEntry.get")  
    @patch("models.pynamodb_model.UserEntry.get")      
    def test_generate_custom_url_with_collision(self, mock_user, mock_get):
        mock_get.return_value = UrlEntry(short_url="mycustomurl", original_url="https://example.com")
        mock_user.return_value = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")     
        with self.assertRaises(CustomUrlExistsError) as context:
            generate_short_url("https://example.com", "test_user", "mycustomurl")            
        self.assertIn("This custom URL is already in use.", str(context.exception))
        
        #test invalid url format
    def test_generate_short_url_malformed(self):
        user = UserEntry(user_id="test_user", url_limit=5, url_count=1, hashed_password="fakehash")
        with self.assertRaises(ValueError) as context:
            generate_short_url("example.com", user.user_id)
        self.assertIn("Input should be a valid URL", str(context.exception))
        
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
        
        #test invalid pwd
    def test_create_user_invalid_password(self):
        with self.assertRaises(ValidationError) as context:
            UserRequest(username="ValidUser", password = "$h0Rt")
        self.assertEqual(context.exception.errors()[0]["msg"], "String should have at least 8 characters")     
       
       #test invalid pwd
    def test_create_user_invalid_password2(self):
        with self.assertRaises(ValidationError) as context:
            UserRequest(username="ValidUser", password = "NOdigits!")
        self.assertIn(context.exception.errors()[0]["msg"], "Value error, Password must be between 8 - 15 characters, include at least one uppercase letter, one lowercase letter, one number, and one special character")
        
        #test invalid username
    def test_create_user_invalid_username(self):
        with self.assertRaises(ValidationError) as context:
            UserRequest(username="woo'psie", password = "Valid!Passw0rd")
        self.assertIn(context.exception.errors()[0]["msg"], "Value error, Username must be between 8 - 15 characters and contain only letters and numbers")
        
    @patch("models.pynamodb_model.UrlEntry.scan")
    def test_list_urls(self, mock_scan):
        mock_scan.return_value = [UrlEntry(short_url="short1", original_url="https://example1.com"),
                                  UrlEntry(short_url="short2", original_url="https://example2.com")]
        
        expected_result = {"short1": "https://example1.com",
                           "short2": "https://example2.com"}
        
        result = get_url_list()
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected_result)
        
        
        
    
  
    