# appstorescraperpy
Apple App Store Scraper written in python



## Apple App Store Scraper
This is based on cowboy-bebug's <a href='https://github.com/cowboy-bebug/app-store-scraper'>app-store-scraper </a> (now deprecated) as this is the only project I've seen that is able to retrieve all the App Store reviews. The project is now deprecated and Apple has changed some of the ways to retrieve the data compared to cowboy-bebug's method. 

I initially used this on an Azure Function and I did not implement custom classes and let the caller parse the JSON data themselves. This iteration I included classes to handle the data. 

### To install

```
python3 -m pip install appstorescraperpy
```

## Usage

### Basic usage

To get the app details, ratings, and reviews with this library, you must use the app ID. This can be seen in the URL of the app page.

For example, Facebook's  URL in the App Store is:

```
https://apps.apple.com/us/app/facebook/id284882215
```

The app ID is
```
284882215
```
Sample code

```python
import appstorescraper

# Let's use Facebook's app ID '284882215'
# by default get_app will use country='us'
# you can change the country. just follow ISO 3166 format for the 
# country codes 
app = appstorescraper.get_app(app_id='284882215',country='us')


# you can get the raw data from the app store by doing
print(app.data)

```

### For ratings data
```python

# To get the average ratings
print(app.ratings.average)

# To get each star count you can either
one_star = app.ratings.list[0]
two_star = app.ratings.list[1]
three_star = app.ratings.list[2]
four_star = app.ratings.list[3]
five_star = app.ratings.list[4]

# or you can do
app.ratings.one_star
app.ratings.two_star
app.ratings.three_star
app.ratings.four_star
app.ratings.five_star

# to get the raw data from the App Store
print(app.ratings.data)
```
Sample ratings data

```json
{
    "ariaLabelForRatings": "4.9 stars",
    "ratingCount": 318959,
    "ratingCountList": [
        3925,
        928,
        2700,
        10776,
        300630
    ],
    "value": 4.9
}
```

### For reviews

Reviews are sorted by the most recent review. 

Just a note: the App Store puts out a maximum of 20 reviews per call. This library takes care of that limitation. You can still try to get all reviews with this library, but I had cases where I got blocked by the App Store for calling the API too much

There are two ways to get reviews:

### app.reviews

```python

# By using app.reviews

# This is an iterator so you can use next() 
print(next(app.reviews))

# or use a for loop
for review in app.reviews:
    print(review)

# you can also get the nth review
# note that this will still get all the reviews before it (1-9 will still be loaded and stored)
print(app.reviews[10])

```
#### app.get_reviews()
```python

# By using app.get_reviews()
# This provides more control

# arguments

# count: how many reviews to retrieve, sorted by the most recent review
# offset: which review index to start, useful when you want to get older reviews so you don't have to load other reviews 

# usage
reviews = app.get_reviews(count=100,offset=0)

```

The next ones did not get tested thoroughly so use with caution

### get_countries_with_reviews
This gives you a list of countries which has at least one retrievable review. This is an expensive all as it goes through all countries and get one review for checking

It returns a dictionary list with data
```json
{
    "alpha_2": "{country_code}",
    "name": "{country_name}"
}
```

Sample usage

```python

from appstorescraper.core import AppleScraper

for country in AppleScraper.get_countries_with_reviews(app_id,sleep=1):
    print(country)

```

### check_review_availability
This checks if a given country code has a retrievable review. Note that is still possible for a country to have a rating but no review

Sample usage

```python
from appstorescraper.core import AppleScraper

app_id = '284882215'
print(AppleScraper.check_review_availability(app_id, 'ph'))
```

Sample result
```json
{
    "has_reviews": true,
    "status_code": 200,
    "message": ""
}
```
