from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection

class UserIdIndex(GlobalSecondaryIndex):
    #Index for querying URL entries by user_id
    class Meta:
        index_name = "user_id-index"
        projection = AllProjection()
        
    user_id = UnicodeAttribute(hash_key=True)
    
    
class UrlEntry(Model):
    class Meta:
        table_name = "url-shortener"
        region = "us-east-2"
    
    short_url = UnicodeAttribute(hash_key=True)
    original_url = UnicodeAttribute()
    user_id = UnicodeAttribute()
    user_id_index = UserIdIndex()
    
    
class UserEntry(Model):
    class Meta:
        table_name = "users"
        region = "us-east-2"
    
    user_id = UnicodeAttribute(hash_key=True)
    hashed_password = UnicodeAttribute()
    is_admin = BooleanAttribute(default=False)
    url_limit = NumberAttribute(default=20)
    url_count = NumberAttribute(default=0)
    
        
        


