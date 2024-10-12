from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute


class UrlEntry(Model):
    class Meta:
        table_name = "url-shortener"
        region = "us-east-2"
    
    short_url = UnicodeAttribute(hash_key=True)
    original_url = UnicodeAttribute()
        
        


