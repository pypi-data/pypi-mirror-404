import re
from requests.adapters import HTTPAdapter
import requests
import logging
import pycountry

from urllib3.util.retry import Retry 

import random
import time


# extend AppStoreScraper to get reviews
class AppleScraper:
    __landing_host = "apps.apple.com"
    __request_host = "amp-api-edge.apps.apple.com"
    __scheme = "https"

    __base_landing_url = f"{__scheme}://{__landing_host}"
    __base_request_url = f"{__scheme}://{__request_host}"

    __user_agents = [
    # NOTE: grab from https://bit.ly/2zu0cmU
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    ]
    
    def __get(
        url,
        headers=None,
        params=None,
        total=3,
        backoff_factor=3,
        status_forcelist=[404, 429],
    ) -> requests.Response:
        retries = Retry(
            total=total,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )

        with requests.Session() as s:
            s.mount(AppleScraper.__base_request_url, HTTPAdapter(max_retries=retries))
            logging.debug(f"Making a GET request: {url}")
            return s.get(url, headers=headers, params=params)
            
    def __build_review_url(country,app_id):
        request_path = f"v1/catalog/{country}/apps/{app_id}/reviews"
        return f"{AppleScraper.__base_request_url}/{request_path}"
    
    def __build_landing_url(country,app_id):
        landing_path = f"{country}/app/id{app_id}"
        landing_url = f"{AppleScraper.__base_landing_url}/{landing_path}"
        return landing_url.format(
            country=country, app_id=app_id
        )
    
    def __build_review_header(landing_url,token):
        return {
            "Accept": "application/json",
            "Authorization": token,
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": AppleScraper.__base_landing_url,
            "Referer": landing_url,
            "User-Agent": random.choice(AppleScraper.__user_agents),
        }
    
    def __get_review_token(landing_url):
        res = AppleScraper.__get(landing_url)

        script_path = re.search(r'<script[^>]*\s+src="(\/assets\/.+\.js)"[^>]*><\/script>',res.text)

        if not script_path:
            raise ValueError("Unable to find the script js tag in the landing page")
        
        # get script js content
        scriptjs = AppleScraper.__get(f"{AppleScraper.__base_landing_url}{script_path.group(1)}")

        # get token from script js
        token = re.search(r'const \w+="(\b([A-Za-z0-9\-_]+={0,2}\.[A-Za-z0-9\-_]+={0,2}\.[A-Za-z0-9\-_]+={0,2})\b)";', scriptjs.text).group(1)
        if not token:
            raise ValueError("Unable to find the review token in the script js")
        
        return f"bearer {token}"
            
    def __parse_review_data(res):
        response = res.json()
        response['data']
        return [{'id':data['id']} | data['attributes'] for data in response['data']]

    def __get_next_offset(res):
        response = res.json()
        next_offset = response.get('next')

        if next_offset:
            offset = re.search("^.+offset=([0-9]+).*$", next_offset).group(1)
            return int(offset)
        else:
            return None
    
    def __get_app_reviews_per_country(app_id, country=None, count:int = None,offset:int = 0, sleep:int = 0.3,headers = None):
       
        landing_url = AppleScraper.__build_landing_url(country,app_id)
        review_url = AppleScraper.__build_review_url(country,app_id)
        
        if not headers:
            # build header
            headers = AppleScraper.__build_review_header(landing_url,AppleScraper.__get_review_token(landing_url))

        request_offset = offset
        reviews = []
    
        while True:
            # init request params
            request_params = {
            "l": "en-GB",
            "offset": request_offset,
            "limit": min(count - len(reviews),20) if count else 20,
            "platform": "web",
            "additionalPlatforms": "appletv,ipad,iphone,mac",
            "sort": "recent"
            }

            res = AppleScraper.__get(review_url,
                            headers,
                            request_params)
            
            # parse the review data and append to reviews list
            reviews.extend(AppleScraper.__parse_review_data(res))

            # get the next offset number
            request_offset = AppleScraper.__get_next_offset(res)

            if count and len(reviews) >= count:
                break
            elif request_offset is None:
                break

            if sleep and type(sleep) is int:
                time.sleep(sleep)

        return reviews,request_offset
       
    def check_review_availability(app_id,country,headers = None):

        logging.info(f"Checking review availability for app id '{app_id}' for country code '{country}'")

        landing_url = AppleScraper.__build_landing_url(country,app_id)
        if not headers:
            # build headers
            headers = AppleScraper.__build_review_header(landing_url,AppleScraper.__get_review_token(landing_url))

        avail_params = {
            "l": "en-GB",
            "platform": "web",
            "additionalPlatforms": "appletv,ipad,iphone,mac"}
        
        # check app availability
        avail_url = AppleScraper.__build_review_url(country,app_id)

        result = requests.get(url=avail_url
                            ,headers=headers,
                            params=avail_params)
        
        if result.status_code == 200:
            logging.info(f"App ID {app_id} has reviews for country '{country}'")

        return {"has_reviews":result.status_code == 200,
                "status_code":result.status_code,
                "message": result.text if result.status_code != 200 else ''}

    def get_countries_with_reviews(app_id,sleep:float=0.5):
        '''
        This gives you a list of countries which has at least one retrievable review. This is an expensive all as it goes through all countries and get one review for checking

        It returns a dictionary list with data

        ```
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

        arguments
        
        app_id: string. The app ID can be seen in the URL of the app page.

        For example, Facebook's  URL in the App Store is:

        ```
        https://apps.apple.com/us/app/facebook/id284882215
        ```

        It's app ID is 
        ```
        284882215
        ```

        sleep: float. Determines interval (in seconds) before attempting another call
        '''
        for country in pycountry.countries:
            res = AppleScraper.check_review_availability(app_id,country.alpha_2.lower())
            if res['has_reviews']:
                yield {'alpha_2':country.alpha_2.lower(),'name':country.name}

            if sleep and type(sleep) is int:
                time.sleep(sleep)
   
    def _get_app_reviews(app_id,count:int = None,sleep:int = 0.3):
        reviews = []
        offset = 0
        for country in pycountry.countries:
            
            landing_url = AppleScraper.__build_landing_url(country.alpha_2.lower(),app_id)
            
            # build header
            headers = AppleScraper.__build_review_header(landing_url,AppleScraper.__get_review_token(landing_url))

            if not AppleScraper.check_review_availability(app_id,country.alpha_2.lower(),headers)['has_reviews']:
                continue

            logging.info(f'Retrieving reviews of app id {app_id} for country {country.name}')
            res,offset = AppleScraper.__get_app_reviews_per_country(app_id,country.alpha_2.lower(),count,offset,sleep,headers)
            reviews.extend(res)

            if count and len(reviews) >= count:
                break
            
        return reviews

    def _get_app_reviews_per_country(app_id, country=None, count:int = None,offset:int = 0, sleep:int = 0.3):
        landing_url = AppleScraper.__build_landing_url(country,app_id)
        # build header
        headers = AppleScraper.__build_review_header(landing_url,AppleScraper.__get_review_token(landing_url))

        if not AppleScraper.check_review_availability(app_id,country,headers)['has_reviews']:
            raise ValueError(f'No reviews found for country code {country}')
        
        return AppleScraper.__get_app_reviews_per_country(app_id,country,count,offset,sleep)
   
    def _get_app_details(app_id,country):
        url = f"{AppleScraper.__base_request_url}/v1/catalog/{country}/apps/{app_id}"

        # generate token
        landing_url = AppleScraper.__build_landing_url(country,app_id)
        # build header
        headers = AppleScraper.__build_review_header(landing_url,AppleScraper.__get_review_token(landing_url))

        request_params = {
            "l": "en-GB",
            "platform": "web",
            "additionalPlatforms": "appletv,ipad,iphone,mac",
            }
        
        res = AppleScraper.__get(url,headers,params = request_params)

        return res.json()['data'][0]
