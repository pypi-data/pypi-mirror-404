import appstorescraper

import logging

app_id = '284882215'
app_name = 'Facebook'

def test_getappdetails():

    try:
        app = appstorescraper.get_app(app_id)

        logging.info(f'App name: {app.name} | App ID: {app.id}')
        assert app.name == app_name

    except Exception as e:
        logging.error(e)
        assert False

    
def test_getappratings():
    try:
        app = appstorescraper.get_app(app_id=app_id)
        logging.info(f'App name: {app.name} | App ID: {app.id} | Ave rating: {app.ratings.average}')
        logging.info('1-star:{0} | 2-star:{1} | 3-star: {2} | 4-star: {3} | 5-star: {4}'.format(*app.ratings.list))
        assert True

    except Exception as e:
        logging.error(e)
        assert False

def test_getreviews_base():

    app = appstorescraper.get_app(app_id=app_id)
    logging.info(f'App name: {app.name} | App ID: {app.id} | Ave rating: {app.ratings.average}')

    review_data = app.get_reviews()

    for review in review_data[0]:
        logging.info(f'Title: {review.title} | Review: {review.content}')

    logging.info(f'Offset: {review_data[1]}')
    
    assert True
    

def test_getreview_app():
    app = appstorescraper.get_app(app_id)
    logging.info(f'App name: {app.name} | App ID: {app.id} | Ave rating: {app.ratings.average}')
    logging.info('1-star:{0} | 2-star:{1} | 3-star: {2} | 4-star: {3} | 5-star: {4}'.format(*app.ratings.list))

    review = next(app.reviews)
    logging.info(f'Title: {review.title} | Review: {review.content}')

    assert True

def test_getreviews_app():
    app = appstorescraper.get_app(app_id)
    logging.info(f'App name: {app.name} | App ID: {app.id} | Ave rating: {app.ratings.average}')
    logging.info('1-star:{0} | 2-star:{1} | 3-star: {2} | 4-star: {3} | 5-star: {4}'.format(*app.ratings.list))

    for _ in range(30):  
        review = next(app.reviews)
        logging.info(f'Title: {review.title} | Review: {review.content}')

    
    assert True


def test_getnthreview():
    app = appstorescraper.get_app(app_id)
    logging.info(f'App name: {app.name} | App ID: {app.id} | Ave rating: {app.ratings.average}')
    logging.info('1-star:{0} | 2-star:{1} | 3-star: {2} | 4-star: {3} | 5-star: {4}'.format(*app.ratings.list))
    logging.info('Get 31st review')
    review = app.reviews[31]
    logging.info(f'Title: {review.title} | Review: {review.content}')

    assert True

def test_get_countries_with_reviews():
    assert True
    return
    from appstorescraper.core import AppleScraper
    
    for country in AppleScraper.get_countries_with_reviews(app_id,sleep=1):
        logging.info(country)


def test_check_review_availability():
    from appstorescraper.core import AppleScraper
    logging.info(AppleScraper.check_review_availability(app_id, 'ph'))
    assert True

    