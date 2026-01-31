from .rating import Rating
from .reviews import Reviews
from .review import Review
from typing import List

from ..core import AppleScraper

class App:

    def __init__(self,data,country):
        self.__data:object = data
        self.__country = country
        self.__reviews:Reviews = None
    
    @property
    def id(self):
        return self.__data['id']

    @property
    def country(self):
        return self.__country

    @property
    def data(self):
        '''
        The raw JSON data of the app details as scraped from the App store
        
        '''
        return self.__data
    
    @property
    def name(self):
        return self.__data['attributes']['name']
    
    @property
    def url(self):
        
        return self.__data['attributes']['url']

    @property
    def ratings(self) -> Rating:
        _ratings = Rating(self.__data['attributes']['userRating'])

        return _ratings

    @property
    def reviews(self) -> Reviews:
        '''
        ### By using app.reviews

        ### This is an iterator so you can use next() 
        ```python
        print(next(app.reviews))
        ```

        ### or use a for loop
        ```python
        for review in app.reviews:
            print(review)
        ```

        ### you can also get the nth review
        note that this will still get all the reviews before it (1-9 will still be loaded and stored)
        ```python
        print(app.reviews[10])
        ```
        
        '''
        if not self.__reviews:
            self.__reviews = Reviews(self)

        return self.__reviews
    

    def get_reviews(self,count=20,offset=0) -> tuple[List['Review'], int]:
        '''
        ### By using app.get_reviews()
        ### This provides more control

        #### arguments

        count: how many reviews to retrieve, sorted by the most recent review
        
        offset: which review index to start, useful when you want to get older reviews so you don't have to load other reviews 

        #### usage
        ```python
        reviews = app.get_reviews(count=100,offset=0)
        ```
        '''
        review_data = AppleScraper._get_app_reviews_per_country(self.id,self.country,count,offset)
        
        reviews = []
        for data in review_data[0]:
            reviews.append(Review(data, self))
        return reviews, review_data[1]

    
