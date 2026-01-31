import datetime
import json

class Review:

    def __init__(self,data,app):
        self._app = app
        self._data = data

    def __str__(self):
        return json.dumps(self._data,indent=1)

    @property
    def app(self):
        return self._app
    
    @property
    def data(self):
        return self._data
    
    @property
    def id(self):
        return self._data['id']
    
    @property
    def date(self) -> datetime.datetime:
        return datetime.datetime.fromisoformat(self._data['date'])
    
    @property
    def is_edited(self) -> bool:
        return self._data['isEdited']
    
    @property
    def rating(self) -> int:
        return self._data['rating']
    
    @property
    def content(self):
        return self._data['review']
    
    @property
    def title(self):
        return self._data['title']
    
    @property
    def username(self):
        return self._data['userName']
    