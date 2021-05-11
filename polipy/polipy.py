from .networking import get_url_type, parse_url, scrape
from .extractors import extract, extractors
from .constants import UTC_DATE, CWD
from .exceptions import NetworkIOException
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
    url : str
        The URL to the privacy policy.
    url_meta : dict or None
        Additional information about the URL, such as domain, scheme, content-type, etc.
    source : str or None
        Policy page source.
    content : str or None
        Text of the policy extracted from the page source.
    """

    url, source, content = {}, {}, {}

    def __init__(self, url):
        """
        Constructor method.

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

    def scrape(self, timeout=30, **kwargs):
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
        self.url['type'], self.source['static_html'] = get_url_type(self.url['url'], timeout)
        if self.url['type'] in ['html', 'pdf']:
            self.source = self.source | scrape(self.url['url'], timeout=timeout, **kwargs)
        else:
            self.source['dynamic_html'] = self.source['static_html']
        return self

    def extract(self, extractors=['text'], **kwargs):
        """
        Extracts content from the page source of the privacy policy.

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
        vargs = {
            'url': self.url['url'],
            'url_type': self.url['type'],
            'static_source': self.source['static_html'],
            'dynamic_source': self.source['dynamic_html'],
            **kwargs
        }
        for extractor in extractors:
            content = extract(extractor, **vargs)
            self.content[extractor] = content
        return self

    def save(self, output_dir, **kwargs):
        """
        ...

        Returns
        -------
        dict
            Dictionary containing policy attributes as key-value pairs.
        """
        # Define output formats.
        output = {
            'html': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'html')),
            'png': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'png')),
            'json': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'json')),
            'pdf': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'pdf')),
            'txt': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'txt')),
            'meta': os.path.join(output_dir, '{}.{}'.format(UTC_DATE, 'meta')),
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
def get_policy(url, screenshot=False, extractors=[], timeout=30, **kwargs):
    """
    Helper method that returns a `polipy.Policy` object containing
    information about the policy, scraped and processed from the given URL.

    Parameters
    ----------
    url : str
        The URL of the privacy policy.

    **kwargs : dict
        Keyword arguments.

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
    policy.scrape(screenshot=screenshot, timeout=timeout)
    policy.extract(extractors=extractors)
    return policy

# def download_policy(url, output_dir=CWD, force=False, skip_errors=True, verbose=False, **kwargs):
def download_policy(url, output_dir=CWD, force=False, skip_errors=True, logger=None, **kwargs):
    # Get handle on the logger object.
    logger = logger if logger is not None else logging.getLogger('polipy')

    # Get policy object with the associated URL.
    policy = Policy(url)

    # Create the output directory if it does not exist.
    d, h = policy.url['domain'].replace('.', '_'), policy.url['hash']
    policy_output_dir = os.path.join(output_dir, '{}_{}'.format(d, h))
    pathlib.Path(policy_output_dir).mkdir(parents=True, exist_ok=True)

    # Skip scraping if policy was already scraped today unless force flag is set.
    files = [x for x in os.listdir(policy_output_dir) if x.split('.')[0] == UTC_DATE]
    if len(files) > 0 and not force:
        logger.warning('Privacy policy was already scraped today from {} -- skipping.'.format(url))
        return

    # Scrape the policy.
    try:
        policy.scrape(**kwargs)
    except NetworkIOException as e:
        if skip_errors:
            logger.warning('Encountered a network exception while scraping policy from {} -- skipping.\n{}'.format(url, e))
            return
        raise e from None

    # Extract information from policy.
    policy.extract(**kwargs)

    # Skip saving the file if the policy did not change unless force flag is set.
    files = [x for x in os.listdir(policy_output_dir) if x.endswith('.json')]
    if len(files) > 0 and not force:
        latest_file = sorted(files, key=lambda x: int(x.split('.')[0]))[-1]
        with open(os.path.join(policy_output_dir, latest_file), 'r') as f:
            last_policy = json.load(f)
        if 'text' in last_policy and (last_policy['text'] == policy.content['text']):
            logger.warning('Privacy policy has not changed since {} for {} -- skipping.'.format(latest_file.split('.')[0], url))
            return

    logger.info('Saving privacy policy obtained from {}.'.format(url))
    policy.save(output_dir=policy_output_dir)
