from .networking import get_url_type, parse_url, scrape_html
from .extractors import extract_html, extract_pdf

# Public module class.
class Policy:
    """
    A class representing a privacy policy.

    Attributes
    ----------
    url : str
        The URL to the privacy policy.
    url_meta : dict or None
        Additional information about the URL, such as domain, scheme, content-type, etc.
    source : str or None
        Policy page source.
    content : str or None
        Text of the policy extracted from the page source.
    """

    url, url_meta = None, None
    source, content = None, None
    _static = None

    def __init__(self, url):
        """
        Constructor method.

        Parameters
        ----------
        url : str
            The URL of the privacy policy.
        """
        self.url = url

    def parse_url(self):
        """
        Obtains additional information about the privacy policy URL,
        including content-type, domain, scheme, path, etc.

        Populates the `Policy.url_meta` attribute.

        Returns
        -------
        polipy.Policy
            `Policy` object with the populated attribute.

        Raises
        ------
        ScraperException
            Raised if an error occured while performing networking I/O.
        """
        url_type, source = get_url_type(self.url)
        self.url_meta = parse_url(self.url)
        self.url_meta['type'] = url_type
        self._static = source
        return self

    def scrape(self, timeout=30):
        """
        Obtains the page source of the given privacy policy URL.

        Populates the `Policy.source` attribute.

        Parameters
        ----------
        timeout : int, optional
            The amount of time in seconds to wait for response (default is 30).

        Returns
        -------
        polipy.Policy
            `Policy` object with the populated attribute.

        Raises
        ------
        NetworkIOException
            Raised if an error occured while performing networking I/O.
        """
        if self.url_meta['type'] == 'html':
            self.source = scrape_html(self.url, timeout)
        else:
            self.source = self._static.decode(errors='ignore')
        return self

    def extract(self):
        """
        Extracts the text from the page source of the privacy policy.

        Populates the `Policy.content` attribute.

        Returns
        -------
        polipy.Policy
            `Policy` object with the populated attribute.

        Raises
        ------
        ParserException
            Raised if an error occured while extracting text from page source.
        """
        if self.url_meta['type'] in ['html', 'other']:
            self.content = extract_html(self.source, self.url)
        elif self.url_meta['type'] == 'pdf':
            self.content = extract_pdf(self._static)
        elif self.url_meta['type'] == 'plain':
            self.content = self.source
        return self

    def to_dict(self):
        """
        Converts the `Policy` object to a dictionary.

        Returns
        -------
        dict
            Dictionary containing policy attributes as key-value pairs.
        """
        obj = {
            'url': self.url,
            'url_meta': self.url_meta,
            'source': self.source,
            'content': self.content
        }
        return obj

    def __repr__(self):
        return '{}({})'.format(self.__class__, self.to_dict())

# Public module methods.
def get_policy(url):
    """
    Helper method that returns a `polipy.Policy` object containing
    information about the policy, scraped and processed from the given URL.

    Parameters
    ----------
    url : str
        The URL of the privacy policy.

    Returns
    -------
    polipy.Policy
        Object containing information about the page source and content.
        Please view documentation for `polipy.Policy` class for more information.

    Raises
    ------
    NetworkIOException
        Raised if an error occured while performing networking I/O.

    ParserException
        Raised if an error occured while extracting text from page source.
    """
    policy = Policy(url)
    policy.parse_url()
    policy.scrape()
    policy.extract()
    return policy
