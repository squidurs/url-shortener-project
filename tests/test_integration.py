import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from models.pynamodb_model import UrlEntry
from service.url_service import *
from jose import JWTError, jwt
from main import app

client = TestClient(app)

# Mock admin user
def mock_get_admin_user():
    #mock user object
    return UserEntry(user_id="adminuser", is_admin=True, url_count=3, url_limit=30, hashed_password="fakehash")

# Mock non-admin user
def mock_get_current_user():
    #mock user object
    return UserEntry(user_id="testuser1", is_admin=False, url_count=3, url_limit=30, hashed_password="fakehash")

# Mock expired token
def mock_expired_token():
    expired_token = jwt.encode({"sub": "testuser1", "exp": datetime.utcnow() - timedelta(seconds=1)}, SECRET_KEY, algorithm=ALGORITHM)
    try:
        jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
# Mock invalid token   
def mock_invalid_token():
    raise HTTPException(status_code=401, detail="Could not validate credentials.")

        

class TestIntegration(unittest.TestCase):
    
      
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UserEntry.get")
    @patch("models.pynamodb_model.UserEntry.save")
    def test_create_short_url_no_collision(self, mock_save, mock_user_get, mock_get):
        mock_get.side_effect = UrlEntry.DoesNotExist()
        mock_user = UserEntry(
        user_id="testuser1",
        is_admin=False,
        url_count=3,
        url_limit=30,
        hashed_password="fakehash"
    )
        mock_user_get.return_value = mock_user
        mock_save.return_value = None
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("short_url", data)
        self.assertIn("original_url", data)
        self.assertEqual(data["original_url"], "https://example.com/")
        
    #test create short url (no custom) WITH collision
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UserEntry.get")
    def test_create_short_url_with_collision(self, mock_user_get, mock_get):
        mock_user_get.return_value = UserEntry(
        user_id="testuser1",
        is_admin=False,
        url_count=3,
        url_limit=30,
        hashed_password="fakehash"
    )
        mock_get.side_effect = [UrlEntry.DoesNotExist(), None, UrlEntry.DoesNotExist()]
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
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
    @patch("models.pynamodb_model.UserEntry.get")
    def test_create_short_url_with_custom(self, mock_user_get, mock_save, mock_get):
        mock_user_get.return_value = UserEntry(
        user_id="testuser1",
        is_admin=False,
        url_count=3,
        url_limit=30,
        hashed_password="fakehash"
    )
        mock_get.side_effect = UrlEntry.DoesNotExist()
        mock_save.return_value = None
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "customurl1"})
    
        if response.status_code != 200:
            print("Error detail:", response.json())
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["short_url"], "customurl1")
        self.assertEqual(data["original_url"], "https://example.com/")
    
    #test create custom with collision (custom url is taken)    
    @patch("models.pynamodb_model.UrlEntry.get")
    @patch("models.pynamodb_model.UserEntry.get")
    def test_create_custom_url_with_collision(self, mock_user_get, mock_get):
        mock_user_get.return_value = UserEntry(
        user_id="testuser1",
        is_admin=False,
        url_count=3,
        url_limit=30,
        hashed_password="fakehash"
    )
        mock_get.return_value = UrlEntry(short_url="onetwothree", original_url="https://example.com")
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "onetwothree"})
                      
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertIn("This custom URL is already in use.", data["detail"])
        
    def test_list_urls(self):
        app.dependency_overrides[get_current_user] = mock_get_admin_user
        
        response = client.get("/list-urls")
        if response.status_code == 404:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("url_pairs", data) 
            self.assertIsInstance(data["url_pairs"], dict)
        
    @patch("models.pynamodb_model.UserEntry.get")    
    def test_redirect_short_url(self, mock_user_get):
        mock_user_get.return_value = UserEntry(
        user_id="testuser1",
        is_admin=False,
        url_count=3,
        url_limit=30,
        hashed_password="fakehash"
    )
        app.dependency_overrides[get_current_user] = mock_get_current_user
        generated_url = client.post("/shorten", json={"url": "https://example.com"})
        short_url = generated_url.json()["short_url"]
        response = client.get(f"/{short_url}")
        if response.status_code == 404:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 307)
            
    #Test non-existent short URL
    def test_no_short_url(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        response = client.get("/r/nonexistent_short_url")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("Short URL not found", data["detail"])
        
    #Test malformed URL input
    def test_invalid_short_url(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        response = client.post("/shorten", json={"url": "example.com"})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["detail"][0]["msg"], "Input should be a valid URL, relative URL without a base")
    
    #Test invalid short url length     
    def test_invalid_short_url_length(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        response = client.post("/shorten", json={"url": "https://example.com", "length":  6})
        self.assertEqual(response.status_code, 422)
        data = response.json()       
        self.assertEqual(data["detail"][0]["msg"], "Input should be greater than or equal to 10")
        
    #Test invalid custom url length    
    def test_invalid_custom_url_length(self):
        app.dependency_overrides[get_current_user] = mock_get_current_user
        response = client.post("/shorten", json={"url": "https://example.com", "custom_url": "short"})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["detail"][0]["msg"], "String should have at least 10 characters")
        
        
    #Test url limit enforcement
    @patch("models.pynamodb_model.UserEntry.get")
    def test_url_limit_enforced(self, mock_get_limit):
        mock_get_limit.return_value = UserEntry(user_id="testuser1", is_admin=False, url_count=3, url_limit=3, hashed_password="fakehash")
        # Override the get_current_user dependency
        app.dependency_overrides[get_current_user] = mock_get_current_user

        response = client.post("/shorten", json={"url": "https://example.com"})
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("URL limit reached", data["detail"])
        app.dependency_overrides = {}

    #Test update url limit
    @patch("models.pynamodb_model.UserEntry.get")
    def test_admin_update_url_limit(self, mock_user_to_update):
        mock_user_to_update.return_value = UserEntry(user_id="testuser1", is_admin=False, url_count=3, url_limit=30, hashed_password="fakehash")
        app.dependency_overrides[get_current_user] = mock_get_admin_user

        response = client.post("/update-url-limit", json={"user_to_update": "testuser1", "new_limit": 10})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "User testuser1 limit updated to 10.")
    
    #Test non-admin user cannot update the URL limit
    @patch("models.pynamodb_model.UserEntry.get")
    def test_non_admin_update_url_limit(self, mock_user_to_update):
        mock_user_to_update.return_value = UserEntry(user_id="testuser1", is_admin=False, url_count=3, url_limit=30, hashed_password="fakehash")
        # Override the get_current_user dependency
        app.dependency_overrides[get_current_user] = mock_get_current_user

        response = client.post("/update-url-limit", json={"user_to_update": "testuser1", "new_limit": 10})
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("Admin privileges required", data["detail"])
        app.dependency_overrides={}
       
    # Test expired token for list_my_urls
    def test_list_user_urls_expired_token(self):
        app.dependency_overrides[get_current_user] = mock_expired_token
        response = client.get("/list-my-urls")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("Expired token", data["detail"])
        
        # Test invalid token for list_my_urls
    def test_list_user_urls_invalid_token(self):
        app.dependency_overrides[get_current_user] = mock_invalid_token
        response = client.get("/list-my-urls")
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("Could not validate credentials", data["detail"])
        
    @patch("models.pynamodb_model.UrlEntry.scan")
    def test_list_user_urls(self, mock_scan):
        mock_scan.return_value = [UrlEntry(short_url="short1", original_url="https://example1.com"), 
                                  UrlEntry(short_url="short2", original_url="https://example2.com")]
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = client.get("/list-my-urls")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("url_pairs", data) 
        self.assertIsInstance(data["url_pairs"], dict)
   
    
    
        
    
