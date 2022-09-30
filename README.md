# polipy
PoliPy is a Python library that provides a command-line interface (CLI) and an API to scrape, parse, and analyze privacy policies of different services. It is a maintained library developed as a collaborative effort of researchers at the [Berkeley Lab for Usable and Experimental Security (BLUES)](https://blues.cs.berkeley.edu/) at the [University of California, Berkeley](https://www.berkeley.edu/).

Please read carefully to learn more about properly [citing](#Citations) this library and the [GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/) terms that govern the usage and modification of this software.

## Prerequisites
PoliPy uses `selenium` library to dynamically scrape webpages that host privacy policies. This allows PoliPy to download policies hosted on pages that, for instance, require JavaScript to be enabled. `Selenium` will open the webpage in a private window of Firefox Browser in the background using a `geckodriver` process, allowing the Python script to control the behavior of the browser without having the user interact with it directly. 

To ensure that PoliPy works as intended, first make sure to install [the latest version of the Mozilla Firefox browser](https://www.mozilla.org/en-US/firefox/new/). Afterwards, download [the latest verison of geckodriver](https://github.com/mozilla/geckodriver/releases) for your operating system. You will need to ensure that the `geckodriver` is on the path and can be executed. Refer to [selenium Python API documentation](https://www.selenium.dev/selenium/docs/api/py/) for more information and troubleshooting.

## Installation

You can easily install the library using `pip`:

```bash
pip install polipy
```

You might encounter the following prompt the first time you run PoliPy on MacOS (or a similar prompt on another OS):

<img src="https://i.imgur.com/vI7Qrpy.png" width=300>

This prompt appears as the library is making network requests to the webpages where privacy policy are hosted. Select `Allow` to continue.

## Example

This library can either be used as a command-line interface (CLI):

```bash
$ cat policies.txt
https://docs.github.com/en/github/site-policy/github-privacy-statement

$ polipy policies.txt -s
```

or as an API imported by another module:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
result = polipy.get_policy(url, screenshot=True)

result.save(output_dir='.')
```

Both of these result in the creation of the following output folder:

```bash
├── docs_github_com_c0eb432555
│   ├── 20210511.html
│   ├── 20210511.png
│   ├── 20210511.json
├── └── 20210511.meta
```
where the base file name corresponds to the date the policy was scraped and the file extensions correspond to the following:

* `.html` contains the (dynamic) source of the webpage where privacy policy is hosted
* `.png` contains the screenshot of the webpage
* `.meta` contains information such as the URL of the privacy policy and the date of last scraping
* `.json` contains the content extracted from the privacy policy.

For instance, the `text` key of the JSON in the `.json` file contains the extracted text from the scraped privacy policy:

```
  GitHub Privacy Statement - GitHub Docs
  GitHub Docs
  All products
  GitHub.com
  Getting started
  ...
  Effective date: December 19, 2020
  Thanks for entrusting GitHub Inc. (“GitHub”, “we”) with your source code, your projects, and your personal information. Holding on to your private information is a serious responsibility, and we want you to know how we're handling it.
  All capitalized terms have their definition in
  GitHub’s Terms of Service , unless otherwise noted here.
  ...
  Contact GitHub
  Pricing
  Developer API
  Training
  About
```

## Usage
CLI usage manual is available with the `--help` or `-h` flag:

```bash
$ polipy --help
usage: __main__.py [-h] [--output_dir OUTPUT_DIR] [--timeout TIMEOUT] [--screenshot] [--extractors EXTRACTORS [EXTRACTORS ...]] [--workers WORKERS] [--force] [--raise_errors] [--verbose] input_file

Download privacy policies from URLs contained in the input_file.

positional arguments:
  input_file            Path to file containing a list of newline-separated URLs of privacy policies to scrape.

optional arguments:
  -h, --help            show this help message and exit
  --output_dir OUTPUT_DIR, -o OUTPUT_DIR
                        Path to directory where policies will be saved (default is ...).
  --timeout TIMEOUT, -t TIMEOUT
                        The amount of time in seconds to wait for the HTTP request response (default is 30).
  --screenshot, -s      Capture and save the screenshot of the privacy policy page (default is False).
  --extractors EXTRACTORS [EXTRACTORS ...], -e EXTRACTORS [EXTRACTORS ...]
                        Extractors to use to capture information from the privacy policy (default is [text]).
  --workers WORKERS, -w WORKERS
                        Number of threading workers to use (default is 1).
  --force, -f           Scrape privacy policy again even if it is already scraped or has not been updated (default is False).
  --raise_errors, -r    Raise errors that occur during the scraping and parsing (default is False).
  --verbose, -v         Enable verbose logging (default is False).
```

The following helper methods are available when the PoliPy library is imported:
- [get_policy](#get_policy): Helper method that returns a `polipy.Policy` object containing
  information about the policy, scraped and processed from the given URL.
- [download_policy](#download_policy): Helper method that scrapes, parses, and saves the privacy policy located at the provided <url>.

Additionally, you can directly create `polipy.Policy` objects supporting the following interface:

- [Policy.\_\_init\_\_](#Policy): Constructor method.
- [Policy.scrape](#scrape): Obtains the page source of the given privacy policy URL.
- [Policy.extract](#extract): Extracts information from the scraped privacy policy.
- [Policy.save](#save): Saves the information contained in the `Policy` object.
- [Policy.to_dict](#to_dict): Converts the `Policy` object to a dictionary.

### get_policy
Helper method that returns a `polipy.Policy` object containing information about the policy, scraped and processed from the given URL.

Parameters:
* `url (str)`: The URL of the privacy policy.
* `screenshot (bool, optional)`: Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
* `timeout (int, optional)`: The amount of time in seconds to wait for the HTTP request response (default is `30`).
* `extractors (list of str, optional)`: Extractors to use to capture information from the privacy policy (default is `["text"]`).

Returns:
* `polipy.Policy`: Object containing information about the privacy policy.

Raises:
* `polipy.NetworkIOException`: Raised if an error has occurred while performing networking I/O.
* `polipy.ParserException`: Raised if an error occurred while extracting text from page source.

### download_policy
Helper method that scrapes, parses, and saves the privacy policy located at the provided `url` by creating the following directory structure:
```
├── <output_dir>
│   ├── <policy URL domain>_<hash of policy URL>
│   │   ├── <current UTC date>.html
│   │   ├── <current UTC date>.json
└── └── └── <current UTC date>.meta
```

Parameters:
* `url (str)`: The URL of the privacy policy.
* `output_dir (str, optional)` Path to directory where the policy will be saved (default is the current working directory).
* `force (bool, optional)`: Flag that indicates whether to scrape privacy policy again even if it is already scraped or has not been updated (default is `False`).
* `raise_errors (bool, optional)`: Flag that indicates whether to raise errors that occur during the scraping and parsing (default is `False`).
* `logger (logging.Logger, optional)`: A `logging.Logger` object to handle the logging of events (default is `None`).
* `screenshot (bool, optional)`: Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
* `timeout (int, optional)`: The amount of time in seconds to wait for the HTTP request response (default is `30`).
* `extractors (list of str, optional)`: Extractors to use to capture information from the privacy policy (default is `["text"]`).

Raises:
* `polipy.NetworkIOException`: Raised if an error has occurred while performing networking I/O.
* `polipy.ParserException`: Raised if an error occurred while extracting text from page source.

### Policy

A class representing a privacy policy. Attributes:

* `url (dict)`: Contains the URL to the privacy policy and additional information about the URL, such as domain, scheme, content-type, etc.
* `source (dict)`: Contains the information scraped from the webpage where policy is hosted, such as the HTML (dynamic) source and the screenshot.
* `content (dict)`: Contains the content extracted from the privacy policy website, such as the text of the policy.

#### \_\_init\_\_
Constructor method. Populates the `Policy.url` attribute. Parameters:

* `url (str)`: The URL of the privacy policy.

#### scrape
Obtains the page source of the given privacy policy URL. Populates the `Policy.source` attribute. Parameters:

* `screenshot (bool, optional)`: Flag that indicates whether to capture and save the screenshot of the privacy policy page (default is `False`).
* `timeout (int, optional)`: The amount of time in seconds to wait for the HTTP request response (default is `30`).

Returns:
* `polipy.Policy`: `Policy` object with the populated attribute.

Raises:
* `polipy.NetworkIOException`: Raised if an error has occurred while performing networking I/O.

#### extract
Extracts information from the scraped privacy policy. Populates the `Policy.content` attribute. Parameters:

* `extractors (list of str, optional)`: Extractors to use to capture information from the privacy policy (default is `["text"]`).

Returns:
* `polipy.Policy`: `Policy` object with the populated attribute.

Raises:
* `polipy.ParserException`: Raised if an error occurred while extracting text from page source.

#### save
Saves the information contained in the `Policy` object. Parameters:

* `output_dir (str)`: Path to directory where the policy will be saved.

#### to_dict
Converts the `Policy` object to a dictionary. Returns:

* `dict`: Dictionary containing policy attributes as key-value pairs.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Citations
Any project that uses this library in part or in whole is required to acknowledge the usage of this library. For publications, the following citation can be used:

>Samarin, N., Kothari, S., Siyed, Z., Wijesekera, P., Fischer, J., Hoofnagle, C. and Egelman, S., Investigating the Compliance of Android App Developers with the CCPA.  

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
