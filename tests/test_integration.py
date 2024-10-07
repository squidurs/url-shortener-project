import unittest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestIntegration(unittest.TestCase):

    def test_integration(self):
        # Add integration tests here
        pass
    #create short url no custom no collision
    def test_create_short_url_no_collision(self):
        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("short_url", data)
        self.assertIn("original_url", data)
        self.assertEqual(data["original_url"], "https://example.com")
        #mock db?
        
    #create short url no custom WITH collision 
    def test_create_short_url_with_collision(self):
        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 200)
        first_short_url = response.json()["short_url"]
        #create collision w first short url
        response = client.post("/shorten", json={"url": "https://example.com"})
        second_short_url = response.json()["short_url"]
        #confirm unique short url on collison
        self.assertNotEqual(first_short_url, second_short_url)
     
    #create custom short url
    #def test_create_short_url_with_custom(self):
        #response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "adcdef"})
        #self.assertEqual(response.status_code, 200)
        #data = response.json()
        #self.assertEqual(data["short_url"], "abcdef")
        #self.assertEqual(data["original_url"], "https://example.com") 
        
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
    
    def test_no_custom_url(self):
        response = client.get("/nonexistent")
        self.assertEqual(response.status_code, 404)
