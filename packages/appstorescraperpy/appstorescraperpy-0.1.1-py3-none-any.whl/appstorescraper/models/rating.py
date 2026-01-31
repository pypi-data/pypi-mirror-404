from typing import List

class Rating:
    
    def __init__(self, data):
        self._data = data


    @property
    def data(self):
        return self._data
    
    @property
    def count(self) -> int:
        return self._data['ratingCount']
    
    @property
    def average(self) -> float:
        return self._data['value']
    
    @property
    def list(self) -> List[int]:
        return self._data['ratingCountList']

    @property
    def one_star(self) -> int:
        return self._data['ratingCountList'][0]
    
    @property
    def two_star(self) -> int:
        return self._data['ratingCountList'][1]
    
    @property
    def three_star(self) -> int:
        return self._data['ratingCountList'][2]
    
    @property
    def four_star(self) -> int:
        return self._data['ratingCountList'][3]
    
    @property
    def five_star(self) -> int:
        return self._data['ratingCountList'][4]