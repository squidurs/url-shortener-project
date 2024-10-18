from models.pynamodb_model import UrlEntry
from pydantic import HttpUrl, ValidationError
import uuid


def generate_short_url(url: str, custom_url: str = None, short_id_length: int = 10) -> str:
    """Generates a short URL for a given original URL.

    Args:
        url (str): The original URL to be shortened.
        custom_url (str, optional): A custom short URL provided by the user. Defaults to None.
        short_id_length (int, optional): The length of the generated short URL if not using a custom URL. Defaults to 10.

    Raises:
        ValueError: If the custom URL already exists in the database.
        ValueError: If the provided URL format is invalid or there is an error generating a unique ID.

    Returns:
        str: The generated or custom short URL that maps to the original URL.
    """
    try:
        valid_url = HttpUrl(url=url)
        url = valid_url.__str__()
        
        if custom_url:
            #check if custom url already exists in db
            try:
                UrlEntry.get(custom_url)
                raise ValueError("This custom URL is already in use.")
            #if custom_url not in database:
            except UrlEntry.DoesNotExist:
                url_entry = UrlEntry(short_url=custom_url, original_url=url)            
                url_entry.save()            
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
                    url_entry = UrlEntry(short_url=unique_id, original_url=url)                    
                    url_entry.save()                    
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
    
    
def delete_url(short_url) -> str:
    """Deletes a given short URL from the database.

    Args:
        short_url (str): The short URL to delete.

    Raises:
        ValueError: If the short URL is not provided.
        ValueError: If the short URL does not exist in the database.
        ValueError: For any other general errors during deletion.

    Returns:
        str: A message confirming whether the deletion was successful.
    """
    try:
        if short_url:
            url = UrlEntry.get(short_url)
            url.delete()
            if UrlEntry.exists(short_url):
                return f"Failed to delete {short_url}."
            else:
                return f"{short_url} was successfully deleted."
        else:
            raise ValueError("Short URL is required.")
    except UrlEntry.DoesNotExist:
        raise ValueError("Could not retrieve or save the URL")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
