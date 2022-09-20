#!/usr/bin/env python3
import argparse
import concurrent.futures

from tqdm import tqdm
from functools import partial

from .polipy import *
from .constants import UTC_DATE, CWD
from .logger import get_logger

def _setup_parser():
    """
    Sets up the CLI argument parser.
    """
    parser = argparse.ArgumentParser(description='Download privacy policies from URLs contained in the `input_file`.')
    parser.add_argument('input_file', help='Path to file containing a list of newline-separated URLs of privacy policies to scrape.')
    parser.add_argument('--output_dir', '-o', default=CWD, help='Path to directory where policies will be saved (default is {}).'.format(CWD))
    parser.add_argument('--timeout', '-t', default=30, type=int, help='The amount of time in seconds to wait for the HTTP request response (default is 30).')
    parser.add_argument('--screenshot', '-s', action='store_true', help='Capture and save the screenshot of the privacy policy page (default is False).')
    parser.add_argument('--extractors', '-e', nargs='+', default=['text'], help='Extractors to use to capture information from the privacy policy (default is ["text"]).')
    parser.add_argument('--workers', '-w', default=1, type=int, help='Number of threading workers to use (default is 1).')
    parser.add_argument('--force', '-f', action='store_true', help='Scrape privacy policy again even if it is already scraped or has not been updated (default is False).')
    parser.add_argument('--raise_errors', '-r', action='store_true', help='Raise errors that occur during the scraping and parsing (default is False).')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (default is False).')
    return parser

class CommandLineTool:

    def __init__(self):
        """
        Sets up the command line tool and handles logging and argument parsing.
        """
        parser = _setup_parser()
        args = parser.parse_args()
        vargs = {k:v for k, v in vars(args).items() if v is not None}
        vargs['logger'] = get_logger(args.verbose)
        self.policies(**vargs)

    def policies(self, input_file, workers, **kwargs):
        """
        Loads the provided list of URLs from the `input_file`, obtains the
        requested information for each policy and saves the
        resulting file to a directory in `output_dir` (defaults to current working directory).
        """
        # Load the list of policy URLs.
        with open(input_file, 'r') as f:
            urls = set([x.strip() for x in f.read().strip().split()])

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(download_policy, url, **kwargs) for url in urls}
            list(tqdm(concurrent.futures.as_completed(futures), total=len(futures)))


def main():
    CommandLineTool()

if __name__ == "__main__":
    main()
