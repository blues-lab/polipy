from .networking import get_url_type, parse_url, scrape
from .extractors import extract, extractors
from .constants import UTC_DATE, CWD
from .exceptions import NetworkIOException, ParserException
from .logger import get_logger

import os
import json
import pathlib
import hashlib
import logging

# Public module class.
class Policy:
    """
    A class representing a privacy policy.

    Attributes
    ----------
    url : dict
        Contains the URL to the privacy policy and additional information about the URL, such as domain, scheme, content-type, etc.
    source : dict
        Contains the information scraped from the webpage where policy is hosted, such as the HTML (dynamic) source and the screenshot.
    content : dict
        Contains the content extracted from the privacy policy website, such as the text of the policy.
    """

    url, source, content = {}, {}, {}

    def __init__(self, url):
        """
        Constructor method. Populates the `Policy.url` attribute.

        Parameters
        ----------
        url : str
            The URL of the privacy policy.
        """
        self.url['url'] = url
        self.url = self.url | parse_url(url)
        self.url['domain'] = self.url['domain'].strip().strip('.').strip('/')

        # Generate the hash to avoid collisions in output file names.
        self.url['hash'] = hashlib.md5(url.encode()).hexdigest()[:10]

        # Define the output directory name for this policy.
        d, h = self.url['domain'].replace('.', '_'), self.url['hash']
        self.output_dir = '{}_{}'.format(d, h)

    def scrape(self, screenshot=False, timeout=30):
        """
        Obtains the page source of the given privacy policy URL.

        Populates the `Policy.source` attribute.

        Parameters
        ----------
        screenshot : bool, optional
            Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
        timeout : int, optional
            The amount of time in seconds to wait for the HTTP request response (default is `30`).
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        polipy.Policy
            `Policy` object with the populated attribute.

        Raises
        ------
        NetworkIOException
            Raised if an error occured while performing networking I/O.
        """
        self.url['type'], self.source['static_html'] = get_url_type(self.url['url'], timeout)
        if self.url['type'] in ['html', 'pdf']:
            self.source = self.source | scrape(self.url['url'], screenshot=screenshot, timeout=timeout)
        else:
            self.source['dynamic_html'] = self.source['static_html']
        return self

    def extract(self, extractors=['text']):
        """
        Extracts information from the scraped privacy policy.

        Populates the `Policy.content` attribute.

        Parameters
        ----------
        extractors : list of str, optional
            Extractors to use to capture information from the privacy policy (default is ["text"]).
        **kwargs : dict
            Additional keyword arguments.

        Returns
        -------
        polipy.Policy
            `Policy` object with the populated attribute.

        Raises
        ------
        ParserException
            Raised if an error occured while extracting text from page source.
        """
        vargs = {
            'url': self.url['url'],
            'url_type': self.url['type'],
            'static_source': self.source['static_html'],
            'dynamic_source': self.source['dynamic_html'],
        }
        for extractor in extractors:
            content = extract(extractor, **vargs)
            self.content[extractor] = content
        return self

    def save(self, output_dir, **kwargs):
        """
        Saves the information contained in the `Policy` object using the following directory structure:

        ├── <output_dir>
        │   ├── <policy URL domain>_<hash of policy URL>
        │   │   ├── <current UTC date>.html
        │   │   ├── <current UTC date>.json
        └── └── └── <current UTC date>.meta

        Parameters
        ----------
        output_dir : str
            Path to directory where the policy will be saved.
        **kwargs : dict
            Additional keyword arguments.
        """
        # Create the output directory if it does not exist.
        policy_output_dir = os.path.join(output_dir, self.output_dir)
        pathlib.Path(policy_output_dir).mkdir(parents=True, exist_ok=True)

        # Define output formats.
        output = {
            'html': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'html')),
            'png': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'png')),
            'json': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'json')),
            'pdf': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'pdf')),
            'txt': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'txt')),
            'meta': os.path.join(policy_output_dir, '{}.{}'.format(UTC_DATE, 'meta')),
        }

        meta = {'last_scraped': UTC_DATE} | self.url

        # Save results.
        if 'dynamic_html' in self.source and self.source['dynamic_html'] is not None:
            with open(output['html'], 'w') as f:
                f.write(self.source['dynamic_html'])
        if 'png' in self.source and self.source['png'] is not None:
            with open(output['png'], 'wb') as f:
                f.write(self.source['png'])
        if len(self.content) > 0:
            with open(output['json'], 'w') as f:
                json.dump(self.content, f)
        if self.url['type'] == 'pdf' and 'static_html' in self.source and self.source['static_html'] is not None:
            with open(output['pdf'], 'w') as f:
                f.write(self.source['static_html'])
        if self.url['type'] == 'plain' and 'static_html' in self.source and self.source['static_html'] is not None:
            with open(output['txt'], 'w') as f:
                f.write(self.source['static_html'])
        if len(self.url) > 0:
            with open(output['meta'], 'w') as f:
                json.dump(meta, f)

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
            'source': self.source,
            'content': self.content
        }
        return obj

    def __repr__(self):
        return '{}({})'.format(self.__class__, self.to_dict())

# Public module methods.
def get_policy(url, screenshot=False, timeout=30, extractors=['text'], **kwargs):
    """
    Helper method that returns a `polipy.Policy` object containing
    information about the policy, scraped and processed from the given URL.

    Parameters
    ----------
    url : str
        The URL of the privacy policy.
    screenshot : bool, optional
        Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
    timeout : int, optional
        The amount of time in seconds to wait for the HTTP request response (default is `30`).
    extractors : list of str, optional
        Extractors to use to capture information from the privacy policy (default is `["text"]`).
    **kwargs : dict
        Additional keyword arguments.

    Returns
    -------
    polipy.Policy
        Object containing information about the privacy policy.
        Please view documentation for `polipy.Policy` class for more information.

    Raises
    ------
    NetworkIOException
        Raised if an error occured while performing networking I/O.

    ParserException
        Raised if an error occured while extracting text from page source.
    """
    policy = Policy(url)
    policy.scrape(screenshot=screenshot, timeout=timeout)
    policy.extract(extractors=extractors)
    return policy

def download_policy(url, output_dir=CWD, force=False, raise_errors=False, logger=None, screenshot=False, timeout=30, extractors=['text'], **kwargs):
    """
    Helper method that scrapes, parses, and saves the privacy policy located at the provided `url`
    by creating the following directory structure:

    ├── <output_dir>
    │   ├── <policy URL domain>_<hash of policy URL>
    │   │   ├── <current UTC date>.html
    │   │   ├── <current UTC date>.json
    └── └── └── <current UTC date>.meta

    Parameters
    ----------
    url : str
        The URL of the privacy policy.
    output_dir : str, optional
        Path to directory where the policy will be saved (default is the current working directory).
    force : bool, optional
        Flag that indicates whether to scrape privacy policy again even if it is already scraped or has not been updated (default is `False`).
    raise_errors : bool, optional
        Flag that indicates whether to raise errors that occur during the scraping and parsing (default is `False`).
    logger : logging.Logger, optional
        A `logging.Logger` object to handle the logging of events (default is `None`).
    screenshot : bool, optional
        Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
    timeout : int, optional
        The amount of time in seconds to wait for the HTTP request response (default is `30`).
    extractors : list of str, optional
        Extractors to use to capture information from the privacy policy (default is `["text"]`).
    **kwargs : dict
        Additional keyword arguments.

    Raises
    ------
    NetworkIOException
        Raised if an error occured while performing networking I/O.

    ParserException
        Raised if an error occured while extracting text from page source.
    """
    # Get handle on the logger object.
    logger = logger if logger is not None else logging.getLogger('polipy')

    # Get policy object with the associated URL.
    policy = Policy(url)

    # Get a handle on the output directory name for this policy.
    policy_output_dir = os.path.join(output_dir, policy.output_dir)
    files = os.listdir(policy_output_dir) if os.path.isdir(policy_output_dir) else []

    # Skip scraping if policy was already scraped today unless force flag is set.
    N = len([x for x in files if x.split('.')[0] == UTC_DATE])
    if N > 0 and not force:
        logger.info('Privacy policy was already scraped today from {} -- skipping.'.format(url))
        return

    # Scrape the policy.
    try:
        policy.scrape(screenshot=screenshot, timeout=timeout)
    except NetworkIOException as e:
        if raise_errors:
            raise e from None
        logger.warning('Encountered a network exception while scraping policy from {} -- skipping.\n{}'.format(url, e))
        return

    # Extract information from policy.
    policy.extract(extractors=extractors)

    # Skip saving the file if the policy did not change unless force flag is set.
    N = len([x for x in files if x.endswith('.json')])
    if N > 0 and not force:
        latest_file = sorted(files, key=lambda x: int(x.split('.')[0]))[-1]
        with open(os.path.join(policy_output_dir, latest_file), 'r') as f:
            last_policy = json.load(f)
        if 'text' in last_policy and (last_policy['text'] == policy.content['text']):
            logger.info('Privacy policy has not changed since {} for {} -- skipping.'.format(latest_file.split('.')[0], url))
            return

    logger.info('Saving privacy policy obtained from {} to {}.'.format(url, os.path.abspath(policy_output_dir)))
    policy.save(output_dir=output_dir)
