from models.pynamodb_model import UrlEntry, UserEntry
from service.utils import *
from pydantic import HttpUrl, ValidationError
import uuid


def generate_short_url(url: str, username: str, custom_url: str = None, short_id_length: int = 10) -> str:
    """Generates a short URL for a given original URL.

    Args:
        url (str): The original URL to be shortened.
        user (UserEntry): The user creating the short URL.
        custom_url (str, optional): A custom short URL provided by the user. Defaults to None.
        short_id_length (int, optional): The length of the generated short URL if not using a custom URL. Defaults to 10.

    Raises:
        ValueError: If the user's URL limit is reached.
        ValueError: If the custom URL already exists in the database.
        ValueError: If the provided URL format is invalid or there is an error generating a unique ID.

    Returns:
        str: The generated or custom short URL that maps to the original URL.
    """
    try:
        valid_url = HttpUrl(url=url)
        url = valid_url.__str__()
        
        user = get_user(username)
        
        if user.url_limit <= user.url_count:
            raise ValueError("URL limit reached.")
        
        if custom_url:
            #check if custom url already exists in db
            try:
                UrlEntry.get(custom_url)
                raise ValueError("This custom URL is already in use.")
            #if custom_url not in database:
            except UrlEntry.DoesNotExist:
                url_entry = UrlEntry(short_url=custom_url, original_url=url, user_id=user.user_id)            
                url_entry.save()   
                user.url_count += 1
                user.save()         
                return custom_url
        else:
            unique_id = str(uuid.uuid4())[:short_id_length]
            #check if the unique id already exists in db
            while True:
                try: 
                    UrlEntry.get(unique_id)
                    #if the above line executes, the unique id was already in db and a new one needs to be generated
                    unique_id = str(uuid.uuid4())[:short_id_length]
                #A unique id has been found
                except UrlEntry.DoesNotExist:
                    #save the unique id to the db
                    url_entry = UrlEntry(short_url=unique_id, original_url=url, user_id=user)                    
                    url_entry.save() 
                    user.url_count += 1
                    user.save()                   
                    return unique_id
        
    except ValidationError:
        raise ValueError("Invalid URL format")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
        

def get_original_url(short_url: str) -> str:
    """Retrieves the original URL associated with a given short URL.

    Args:
        short_url (str): The short URL to look up in the database.

    Raises:
        ValueError: If the short URL does not exist in the database.

    Returns:
        str: The original URL associated with the short URL.
    """
    try:
        #retrieve og url from db
        response = UrlEntry.get(short_url)
        return response.original_url
    except UrlEntry.DoesNotExist:
        raise ValueError("Short URL does not exist.")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
    
def get_url_list() -> dict[str, str]:
    """Retrieves all short-original URL pairs from the database.

    Raises:
        ValueError: If there is an error fetching data from the database.

    Returns:
        dict[str, str]: A dictionary with short URLs as keys and their original URLs as values.
    """
    try:
        url_entries = UrlEntry.scan()
        url_dict = {entry.short_url: entry.original_url for entry in url_entries}
        return url_dict
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
    
def get_user_url_list(username: str) -> dict[str, str]:
    """Retrieves all short-original URL pairs for the given user.
    
    Args:
        username (str): The username whose URLs to retrieve.
        
    Raises:
        ValueError: If there is an error fetching data from the database.

    Returns:
        dict[str, str]: A dictionary with short URLs as keys and their original URLs as values.
    """
    try:
        url_entries = UrlEntry.user_id_index.query(username)
        url_dict = {entry.short_url: entry.original_url for entry in url_entries}
        return url_dict
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
    
def delete_url(short_url: str) -> dict:
    """Deletes a given short URL from the database.

    Args:
        short_url (str): The short URL to delete.

    Raises:
        ValueError: If the short URL does not exist in the database.

    Returns:
        dict: A message confirming whether the deletion was successful.
    """
    try:
        
        url_entry = UrlEntry.get(short_url)        
        url_entry.delete()
        
        if UrlEntry.exists(short_url):
            return f"Failed to delete {short_url}."
        else:
            return {"message": f"{short_url} was successfully deleted."}
        
    except UrlEntry.DoesNotExist:
        raise ValueError("Short URL not found")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
    
def create_new_user(username: str, password: str) -> UrlEntry:
    """Creates a new user entry in the database if the username does not already exist.

    Args:
        username (str): The desired username.
        password (str): The user's password, which will be hashed for storage.

    Raises:
        ValueError: If the username already exists or if an invalid format is used.
        RuntimeError: If an error occurs during user creation in the database.

    Returns:
        UserEntry: The created user object.
    """  
    #check if username already exists in db
    try:
        UserEntry.get(username)
        raise ValueError("This username is taken.")
    #if username not in database:
    except UserEntry.DoesNotExist:
        hashed_password = get_password_hash(password)
        new_user = UserEntry(
            user_id=username,
            hashed_password=hashed_password,
            url_limit=20,
            url_count=0,
            is_admin=False                   
        )
        
        try:
            new_user.save()
        except Exception as e:
            raise RuntimeError(f"Failed to create user due to: {str(e)}")
        
        return new_user
                   
    except ValidationError:
        raise ValueError("Invalid User format")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    

def update_password(username: str, new_password: str) -> dict:
    """Updates the password for an authorized user.

    Args:
        username (str): The username whose password is being updated.
        new_password (str): The new password, which will be hashed for storage.

    Raises:
        ValueError: If the user does not exist in the database.

    Returns:
        dict: A message confirming the password update.
    """
    
    new_hashed_password = get_password_hash(new_password)
    
    try:
        user = UserEntry.get(username)
        user.update(actions=[UserEntry.hashed_password.set(new_hashed_password)])
        return {"message": "Password has been updated."}
    except UserEntry.DoesNotExist:
            raise HTTPException(status_code=404, detail="User not found.")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
