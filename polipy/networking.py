import requests
from urllib.parse import urlparse
from .exceptions import NetworkIOException

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

def get_url_type(url, timeout):
    """
    https://stackoverflow.com/questions/38690586/determine-if-url-is-a-pdf-or-html-file
    """
    try:
        r = requests.get(url, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise NetworkIOException(e) from None
    content_type = r.headers.get('content-type', '')
    url_type = None
    if 'application/pdf' in content_type:
        url_type = 'pdf'
    elif 'text/html' in content_type:
        url_type = 'html'
    elif 'text/plain' in content_type:
        url_type = 'plain'
    else:
        url_type = 'other'
    return url_type, r.content.decode(errors='ignore')

def parse_url(url):
    parsed = urlparse(url)
    result = {
        'scheme': parsed.scheme,
        'domain': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': parsed.query,
        'fragment': parsed.fragment,
    }
    return result

def scrape(url, screenshot, timeout, **kwargs):
    options = Options()
    options.add_argument('-headless')
    options.add_argument('-private')
    driver = webdriver.Firefox(options=options)
    driver.set_page_load_timeout(timeout)
    response = {}
    try:
        driver.get(url)
        response['dynamic_html'] = driver.page_source
        response['png'] = driver.get_screenshot_as_png() if screenshot else None
    except (TimeoutException, WebDriverException) as e:
        raise NetworkIOException(e) from None
    finally:
        driver.quit()
    return response
