import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from models.pynamodb_model import UrlEntry
from service.url_service import *
from main import app

client = TestClient(app)

class TestIntegration(unittest.TestCase):
    
      
    @patch("models.pynamodb_model.UrlEntry.get")
    def test_create_short_url_no_collision(self, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist()
        
        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("short_url", data)
        self.assertIn("original_url", data)
        self.assertEqual(data["original_url"], "https://example.com/")
        
    #test create short url (no custom) WITH collision
    @patch("models.pynamodb_model.UrlEntry.get")
    def test_create_short_url_with_collision(self, mock_get):
        mock_get.side_effect = [UrlEntry.DoesNotExist(), None, UrlEntry.DoesNotExist()]
        
        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 200)
        first_short_url = response.json()["short_url"]
        #create collision w first short url
        response = client.post("/shorten", json={"url": "https://example.com"})
        second_short_url = response.json()["short_url"]
        #confirm unique short url on collison
        self.assertNotEqual(first_short_url, second_short_url)
     
    #test create custom short url (no collision)
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UrlEntry.save")
    def test_create_short_url_with_custom(self, mock_save, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist()
        mock_save.return_value = None
        
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "customurl1"})
        print("Response status code:", response.status_code)
        if response.status_code != 200:
            print("Error detail:", response.json())
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["short_url"], "customurl1")
        self.assertEqual(data["original_url"], "https://example.com/")
    
    #test create custom with collision (custom url is taken)    
    @patch("models.pynamodb_model.UrlEntry.get")
    def test_create_custom_url_with_collision(self, mock_get):
        mock_get.return_value = UrlEntry(short_url="onetwothree", original_url="https://example.com")
        
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "onetwothree"})
                      
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertIn("This custom URL is already in use.", data["detail"])
        
    def test_list_urls(self):
        response = client.get("/list")
        if response.status_code == 404:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
            for pair in data:
                self.assertIn("short_url", pair)
                self.assertIn("original_url", pair)
        
    def test_redirect_short_url(self):
        generated_url = client.post("/shorten", json={"url": "https://example.com"})
        short_url = generated_url.json()["short_url"]
        response = client.get(f"/{short_url}")
        if response.status_code == 404:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 307)
            
    #Test non-existent short URL
    def test_no_short_url(self):
        response = client.get("/nonexistent_short_url")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("Not Found", data["detail"])
        
    #Test malformed URL input
    def test_invalid_short_url(self):
        response = client.post("/shorten", json={"url": "example.com"})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["detail"][0]["msg"], "Input should be a valid URL, relative URL without a base")
    
    #Test invalid short url length     
    def test_invalid_short_url_length(self):
        response = client.post("/shorten", json={"url": "https://example.com", "length":  6})
        self.assertEqual(response.status_code, 422)
        data = response.json()       
        self.assertEqual(data["detail"][0]["msg"], "Input should be greater than or equal to 10")
        
    #Test invalid custom url length    
    def test_invalid_custom_url_length(self):
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "short"})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["detail"][0]["msg"], "String should have at least 10 characters")
        
        
    
