# -*- coding: UTF-8 -*-

import argparse
from bs4 import BeautifulSoup
import datetime
import hashlib
import logging
import multiprocessing
import os
import selenium
import sys
import time
import pickle
import tldextract
import queue
import requests
import io

# from pyPdf import PdfFileReader
from tika import parser
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.remote.command import Command

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

###############################################################################
# Define classes.
###############################################################################

class PrivacyPolicy:
    def __init__(self, url, is_active=0):
        self.url = url
        self.url_md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
        self.is_active = is_active

        domain = tldextract.extract(url)
        self.domain = '.'.join(x for x in domain if x is not None).strip().strip('.') # Domains can't start or end with spaces or dots

    def __str__(self):
        return 'url=%s,domain=%s,url_md5=%s,is_active=%d' % (self.url, self.domain, self.url_md5, self.is_active)

    def __hash__(self):
        return hash(self.url_md5)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.url_md5 == other.url_md5

class ParallelArg:
    def __init__(self, policy, output_dir, utc_date=None, check_date=None, browser_language='en-US, en', verbose=False):
        self.policy = policy
        self.output_dir = output_dir
        self.check_date = check_date
        self.utc_date = utc_date
        self.browser_language = browser_language
        self.verbose = verbose

###############################################################################
# Setup and helper functions.
###############################################################################

def _parse_args():
    parser = argparse.ArgumentParser(description='Download privacy policies, optionally update the DB')
    parser.add_argument('input_path', help='Path to file where policy urls are located.')
    parser.add_argument('output_dir', help='Path to directory where policies will be saved. Creates directory structure <outputdir>/<date>/<regiontag>/<domain>/<urlhash>/')
    parser.add_argument('--processes', '-p', default=multiprocessing.cpu_count(), type=int, help='Number of processes to use')
    parser.add_argument('--check_previous', '-c', default=False, action='store_true', help='Boolean indicating whether to check against previous policies')
    parser.add_argument('--language', '-l', default='en-US, en', help='Language string to set in Firefox\'s intl.accept_languages option. Defaults to "en_US, en"')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def _enable_verbose_logging(enable):
    logging.basicConfig()
    if(enable):
        logger.setLevel(logging.INFO)

def get_urls_from_file(input_file):
    # Get information about apps.
    with open(input_file, 'r') as f:
        policy_urls = f.read().split('\n')
    return policy_urls

def _write_file(content, output, write_mode='w'):
    with open(output, write_mode) as out_file:
        out_file.write(content)

###############################################################################
# Content extractors.
###############################################################################

def _extract_pdf(pdf_content):
    """
    From https://stackoverflow.com/questions/45470964/python-extracting-text-from-webpage-pdf
    """
    f = io.BytesIO(pdf_content)

    # First try using Tika parser, which gives better results.
    raw = parser.from_buffer(f)
    content = raw['content'] if 'content' in raw else ''

    # If that does not work, use PdfFileReader. Note: requires many dependencies.
    # reader = PdfFileReader(f)
    # if content is None or content == '':
    #     N = reader.getNumPages()
    #     content = [reader.getPage(i).extractText().strip() for i in range(N)]
    #     content = '\n'.join(content)

    return content.strip()

def _extract_google_docs(html):
    chunks = html.split('"s":"')[1:]
    chunks = [x.split('"},')[0].replace('\\n', '\n').replace('\\u000b', '\n') for x in chunks]
    text = ''.join(chunks).strip()
    return text

def _extract_text(html):
    """
    From https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
    """
    soup = BeautifulSoup(html, 'lxml')

    for script in soup(['script','style']):
        script.extract()

    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text

###############################################################################
# Zombie processes killers.
###############################################################################

def _kill_zombies_parallel_wrapper(q, zombie_timeout=300):
    while True:
        time.sleep(zombie_timeout)
        _kill_zombies(zombie_timeout=zombie_timeout)
        try:
            q.get_nowait()
            logger.info('Kill zombies queue no longer empty, terminating process')
            break
        except queue.Empty:
            continue

def _kill_zombies(zombie_timeout=5):
    if(os.name == 'posix'):
        logger.info('Killing hung geckodriver and firefox processes running for more than %d seconds' % zombie_timeout)
        os.system('ps -eo pid,ppid,etime,command | grep geckodriver | grep -v grep  | awk \'{if (int(substr($3,0,2)) > %d) {print $1,$2}}\' | xargs kill -9 || true > /dev/null 2>&1' % zombie_timeout)
        os.system('ps -eo pid,ppid,etime,command | grep "firefox -marionette" | grep -v grep  | awk \'{if (int(substr($3,0,2)) > %d) {print $1,$2}}\' | xargs kill -9 || true > /dev/null 2>&1' % zombie_timeout)
    else:
        logger.warning('Can\'t kill zombie processes on non-posix system "%s"' % os.name)

###############################################################################
# Main download policy function.
###############################################################################

def download_policy(policy, output_dir, check_date=None, utc_date=None, browser_language='en-US, en', browser_max_tries=10, browser_page_load_timeout=30):
    '''
    Output files:
    <domain>--<identifier>[--<region_tag>]--<utc_date>
    - .html: HTML content dump from URL
    - .txt: Text content extraction from HTML
    - .png: Full-screen content screenshot from URL
    - .url: Text file containing URL
    - .md5: MD5 hex digest of the raw file
    '''
    assert isinstance(policy, PrivacyPolicy), 'policy argument must be of type PrivacyPolicy'
    assert os.path.isdir(output_dir), 'Output directory %s does not exist' % output_dir

    if(utc_date is None):
        utc_date = datetime.datetime.utcnow().strftime('%Y%m%d')
        logger.info('utc_date was None, setting to %s' % utc_date)

    filename_parts = [policy.domain, policy.url_md5, utc_date]
    output_filename = '--'.join(x for x in filename_parts if x is not None)

    logger.info('Downloading privacy policy %s into %s' % (policy.url, output_dir))

    ff_driver = None
    try:
        ff_opts = webdriver.FirefoxOptions()
        ff_opts.add_argument('--headless')
        ff_opts.add_argument('--private')
        ff_prof = webdriver.FirefoxProfile()
        ff_prof.set_preference('intl.accept_languages', browser_language)
        while(ff_driver is None and browser_max_tries > 0):
            try:
                logger.info('Initializing Firefox web driver for %s' % policy.url)
                ff_driver = webdriver.Firefox(options=ff_opts, firefox_profile=ff_prof)
                logger.info('Firefox driver initialized for %s' % policy.url)
            except:
                browser_max_tries = browser_max_tries - 1
                logger.exception('Exception while creating Firefox driver for %s. Will try %d more times.' % (policy.url, browser_max_tries))
        assert ff_driver is not None, 'Firefox web driver failed to initialize for %s' % policy.url
        ff_driver.set_page_load_timeout(browser_page_load_timeout)
        logger.info('Getting %s' % policy.url)
        ff_driver.get(policy.url)
        logger.info('Got %s' % policy.url)

        # Extract text from documents.
        page_source = ff_driver.page_source
        if policy.url.endswith('.pdf'):
            response = requests.get(policy.url, verify=False)
            extracted_text = _extract_pdf(response.content)
        elif policy.domain == 'docs.google.com' and '"s":"' in page_source:
            extracted_text = _extract_google_docs(page_source)
        else:
            extracted_text = _extract_text(page_source)

        # Check if policy has been updated based on the text of the policy.
        check_dir, check_file_path = None, None
        while check_date is not None:
            filename_parts_past = [policy.domain, policy.url_md5, check_date]
            check_filename = '--'.join(x for x in filename_parts_past if x is not None)
            check_output_dir = os.path.abspath(os.path.join(os.path.abspath(output_dir), '..', '..', '..', check_date))
            check_dir = os.path.join(check_output_dir, policy.domain, policy.url_md5)

            if os.path.exists(os.path.join(check_dir, 'output.out')):
                with open(os.path.join(check_dir, 'output.out')) as date_file:
                    check_date = date_file.read()
            else:
                break

        # Check if the current policy matches the previous one, if possible.
        if check_dir is not None and os.path.exists(check_dir):
            check_output_file = '%s.txt' % check_filename
            check_file_path = os.path.join(check_dir, check_output_file)

        # If policy has not been updated, write an output.out file.
        if check_file_path is not None and os.path.exists(check_file_path):
            with open(check_file_path) as prev_txt:
                policy_updated = extracted_text != prev_txt.read()
            if policy_updated:
                logger.info('There is an updated privacy policy for %s - scraping', policy.url)
            else:
                logger.info('No difference found between previous policy for %s - exiting', policy.url)
                _write_file(check_date, os.path.join(output_dir, 'output.out'))
                return

        output_url = '%s.url' % output_filename
        logger.info('Saving %s as URL file %s' % (policy.url, output_url))
        _write_file(policy.url, os.path.join(output_dir, output_url))

        output_html = '%s.html' % output_filename
        logger.info('Saving %s as HTML dump %s' % (policy.url, output_html))
        _write_file(page_source, os.path.join(output_dir, output_html))

        output_txt = '%s.txt' % output_filename
        logger.info('Saving %s as text extraction %s' % (policy.url, output_txt))
        _write_file(extracted_text, os.path.join(output_dir, output_txt))

        output_md5 = '%s.md5' % output_filename
        logger.info('Saving %s\'s MD5 sum as %s' % (policy.url, output_md5))
        file_md5 = hashlib.md5(open(os.path.join(output_dir, output_html), 'rb').read()).hexdigest()
        _write_file(file_md5, os.path.join(output_dir, output_md5))

        output_png = '%s.png' % output_filename
        logger.info('Saving %s as PNG screenshot %s' % (policy.url, output_png))
        ff_html = ff_driver.find_element_by_tag_name('html')
        ff_html.screenshot(os.path.join(output_dir, output_png))

        if not policy.url.endswith('.pdf'):
            return

        output_pdf = '%s.pdf' % output_filename
        logger.info('Saving %s associated PDF file %s' % (policy.url, output_pdf))
        _write_file(response.content, os.path.join(output_dir, output_pdf), write_mode='wb')


    except Exception as e:
        logger.exception('Error while downloading policy.url: %s' % policy.url)

    finally:
        if(ff_driver is not None):
            try:
                logger.info('Closing Firefox web driver for %s' % policy.url)
                ff_driver.quit()
                logger.info('ff_driver.quit() success for %s' % policy.url)
                return
            except:
                logger.exception('Error while closing Firefox web driver for: %s' % policy.url)
        else:
            logger.warning('ff_driver is None for %s' % policy.url)

def _download_policy_parallel_wrapper(parallel_arg):
    logger = logging.getLogger(__name__)
    _enable_verbose_logging(parallel_arg.verbose)

    assert isinstance(parallel_arg, ParallelArg), 'Argument to _download_policy_parallel_wrapper must be of type ParallelArg'

    assert not os.path.isfile(parallel_arg.output_dir), 'Policy output directory %s already exists as a file'
    if(not os.path.isdir(parallel_arg.output_dir)):
        logger.info('Creating policy output directory %s' % parallel_arg.output_dir)
        os.makedirs(parallel_arg.output_dir)
    assert os.path.isdir(parallel_arg.output_dir), 'Policy output directory %s does not exist' % parallel_arg.output_dir

    # Only scrape if empty.
    file_num = len(os.listdir(parallel_arg.output_dir))
    if file_num > 0:
        logger.info('Policy output directory {} has {} files; skipping'.format(parallel_arg.output_dir, file_num))
        return

    download_policy(parallel_arg.policy, \
                    parallel_arg.output_dir, \
                    check_date=parallel_arg.check_date, \
                    utc_date=parallel_arg.utc_date, \
                    browser_language=parallel_arg.browser_language)

def _download_policies(policies, output_dir, language, verbose, check_previous, processes=multiprocessing.cpu_count()):
    unique_policies = set(policies)
    logger.info('Attempting to download %d policies' % len(unique_policies))
    logger.info('output_dir=%s, language=%s' % (output_dir, language))

    # Create the tagged output directory <output_dir>/<date>/<region_tag>/, if necessary
    utc_date = datetime.datetime.utcnow().strftime('%Y%m%d')
    tagged_output_dir = os.path.join(os.path.abspath(output_dir), utc_date) #, region_tag)
    assert not os.path.isfile(tagged_output_dir), 'Tagged output directory %s already exists as a file'
    if(not os.path.isdir(tagged_output_dir)):
        logger.info('Creating tagged output directory %s' % tagged_output_dir)
        os.makedirs(tagged_output_dir)
    assert os.path.isdir(tagged_output_dir), 'Tagged output directory %s does not exist' % tagged_output_dir

    # Set up the process to kill hung geckodrivers
    logger.info('Setting up geckodriver killer')
    queue = multiprocessing.Queue()
    killer_process = multiprocessing.Process(target=_kill_zombies_parallel_wrapper, args=(queue,))
    killer_process.start()

    # Calculate date to check by if update argument is true
    check_date = None
    if check_previous:
        directory_dates = []
        for d in os.listdir(os.path.abspath(output_dir)):
            if d != utc_date:
                try:
                    directory_dates.append(datetime.datetime.strptime(d, '%Y%m%d'))
                except ValueError:
                    pass
        check_date = max(directory_dates).strftime('%Y%m%d') if len(directory_dates) > 0 else None

    # Download the policies
    logger.info('Parallelizing downloads over %d processes' % processes)
    parallel_args = [ParallelArg(x, \
                                 os.path.join(tagged_output_dir, x.domain, x.url_md5), \
                                 utc_date=utc_date, \
                                 browser_language=language, \
                                 check_date=check_date, \
                                 verbose=verbose) \
                     for x in unique_policies]

    with multiprocessing.Pool(processes=processes) as pool:
        r = list(tqdm(pool.imap_unordered(_download_policy_parallel_wrapper, parallel_args), total=len(parallel_args)))

    # Kill the geckodriver killer process
    logger.info('Stopping the geckodriver killer process')
    queue.put(True)
    queue.close()
    queue.join_thread()
    killer_process.join()

###############################################################################
# Main function.
###############################################################################

if __name__ == '__main__':
    args = _parse_args()
    _enable_verbose_logging(enable=True)
    assert (args.output_dir is not None), 'Must specify output directory'
    assert (args.input_path is not None), 'Must specify file containing policy urls'

    processes = args.processes
    if processes is None:
        processes = 1
    assert (isinstance(processes, int) and processes > 0), 'Must specify positive number of processes'

    # Load privacy policies.
    policy_urls = get_urls_from_file(args.input_path)

    # Policy URLs should be list of PrivacyPolicy objects.
    policies = [PrivacyPolicy(url) for url in policy_urls]

    # Download policies
    _download_policies(policies, args.output_dir, args.language, args.verbose, args.check_previous, processes=processes)
