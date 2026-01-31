from .review import Review
from ..core import AppleScraper
import logging

class Reviews:

    def __init__(self, app):
        self.app = app
        self.__current_data = {}

        self.__current_offset = 0
        self.__current_iter = 0
        self.__reviews = []
    
    def __len__(self):
        return len(self.__reviews)
    
    def __getitem__(self, key:int) -> Review:
        last_review_count = 0
        while len(self.__reviews) < key:
            self.__iterate()
            
            if len(self.__reviews) > key:
                break
            
            if last_review_count == len(self.__reviews):
                raise IndexError(f'Cannot retrieve more than {key} reviews')
            
            last_review_count = len(self.__reviews)
        
        return self.__reviews[key]
    
    def __iter__(self):
        return self
    
    def __next__(self) -> Review:

        if self.__current_iter >= len(self.__reviews):
            self.__iterate()
        
        review:Review = self.__reviews[self.__current_iter]

        self.__current_iter += 1

        return review
    
    def __iterate(self):
        logging.debug(f'Retrieving reviews data for app {self.app.name} | Current offset: {self.__current_offset}')
        self.__current_data = AppleScraper._get_app_reviews_per_country(self.app.id,self.app.country,20,self.__current_offset)
        self.__current_offset = self.__current_data[1]

        for review_data in self.__current_data[0]:
            self.__reviews.append(Review(review_data,self.app))



        

    

    
