from models.pynamodb_model import UrlEntry
import uuid
# This is where your URL shortening logic will go
def generate_short_url(url: str, custom_url: str = None, short_id_length: int = 6) -> str:
    # Implement your URL shortening logic here
    try:
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
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
        

def get_original_url(short_url: str) -> str:
    try:
        #retrieve og url from db
        response = UrlEntry.get(short_url)
        return response.original_url
    except UrlEntry.DoesNotExist:
        raise ValueError("Short URL does not exist.")
    
    
def get_url_list() -> dict[str, str]:
    try:
        url_entries = UrlEntry.scan()
        url_dict = {entry.short_url: entry.original_url for entry in url_entries}
        return url_dict
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
    
def delete_url(short_url) -> str:
    try:
        if short_url:
            url = UrlEntry.get(short_url)
            url.delete()
            return f"{short_url} was deleted."
        else:
            raise ValueError("Short URL is required.")
    except UrlEntry.DoesNotExist:
        raise ValueError("Could not retrieve or save the URL")
    except Exception as e:
        raise ValueError(f"Error: {str(e)}")
    
