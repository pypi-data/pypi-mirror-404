from .core import AppleScraper
from .models import App


def get_app(app_id,country='us') -> App:
    '''
    ## get_app(app_id:str, country:str)

    Gets the app details into an App object
    
    app_id: string. The app ID can be seen in the URL of the app page.

    For example, Facebook's  URL in the App Store is:

    ```
    https://apps.apple.com/us/app/facebook/id284882215
    ```

    It's app ID is 
    ```
    284882215
    ```

    country: string. the country code following ISO 3166. If not provided, 'us' will be used as default
    '''
    _details = AppleScraper._get_app_details(app_id,country)

    return App(_details,country)
