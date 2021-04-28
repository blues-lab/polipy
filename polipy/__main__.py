#!/usr/bin/env python3
import os
import sys
import json
import logging
import argparse
from .polipy import *

logger = logging.getLogger(__name__)

def _setup_logger():
    filename = 'output.log'
    datefmt = '%Y-%m-%d %H:%M:%S'
    log_format = '[%(asctime)s] - %(levelname)-8s %(message)s'
    formatter = logging.Formatter(log_format, datefmt)

    file_handler = logging.FileHandler(filename, 'w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.INFO)

def _setup_parsers():
    # Create the top-level parser.
    parser, subparsers = argparse.ArgumentParser(), {}
    handle = parser.add_subparsers(help='Command to pass to the Google Play Store scraper.', dest='command')

    # Create the parser for the 'policy' command.
    subparsers['policy'] = handle.add_parser('policy', help='Retrieves the full detail of an application.')
    subparsers['policy'].add_argument('url', help='The URL of the privacy policy.')

    # Create the parser for the 'policies' command.
    subparsers['policies'] = handle.add_parser('policies', help='Retrieves the full detail of an application.')
    subparsers['policies'].add_argument('--input_path', '-i', required=True, help='Path containing a list of newline-separated URLs of privacy policies.')

    # Add universal commands to all subparsers.
    for subparser in subparsers.values():
        subparser.add_argument('--output_path', '-o', help='', required=True)
        subparser.add_argument('--throttle', default=1, type=int, help='Upper bound to the amount of requests that will be attempted per second.')
        subparser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    return parser, subparsers

class CommandLineTool:

    def __init__(self, parser):
        args = parser.parse_args()
        vargs = {k:v for k, v in vars(args).items() if v is not None}

        # Check if the supplied command is valid.
        if args.command is None or not hasattr(self, args.command):
            print('Unrecognized command: {}.'.format(args.command))
            parser.print_help()
            exit(1)

        logger.setLevel(logging.DEBUG) if args.verbose else logger.setLevel(logging.INFO)
        results = getattr(self, args.command)(**vargs)

        # Save output to file.
        self._save_results(results, args.output_path)

    def policy(self, **kwargs):
        return get_policy(**kwargs).to_dict()

    def policies(self, **kwargs):
        with open(kwargs['input_path'], 'r') as f:
            urls = f.read().strip().split('\n')
        return [self.policy(**{'url': url, **kwargs}) for url in urls]

    def _save_results(self, results, output_path):
        with open(output_path, 'w') as f:
            json.dump(results, f)

def main():
    _setup_logger()
    parser, subparsers = _setup_parsers()
    CommandLineTool(parser)

if __name__ == "__main__":
    main()
