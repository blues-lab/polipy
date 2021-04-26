# polipy
PoliPy is a library for scraping and parsing privacy policy. (TODO)

## Installation

TODO

## Example

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
result = polipy.get_policy(url)

print(result.content)
```

Results:

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
Available class and class-level methods:
- [Policy](#Policy): A class representing a privacy policy.
- [Policy.parse_url](#Policy.parse_url): Obtains additional information about the privacy policy URL.
- [Policy.scrape](#Policy.scrape): Obtains the page source of the given privacy policy URL.
- [Policy.extract](#Policy.extract): Extracts the text from the page source of the privacy policy.
- [Policy.to_dict](#Policy.to_dict): Converts the `Policy` object to a dictionary.

Available module-level methods:
- [get_policy](#get_policy): Helper method that returns a `Policy` object that contains information about the policy scraped and processed from the given URL.

### Policy

A class representing a privacy policy. Parameters:

* `url`: The URL of the privacy policy.

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
policy = polipy.Policy(url=url)

print(policy)
```

Results:

```python
<class 'polipy.polipy.Policy'>(
  {
    'url': 'https://docs.github.com/en/github/site-policy/github-privacy-statement',
    'url_meta': None,
    'source': None,
    'content': None
  }
)
```

### Policy.parse_url

Obtains additional information about the privacy policy URL, including content-type, domain, scheme, path, etc. Populates the `Policy.url_meta` attribute. Parameters:

* this method has no parameters

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
policy = polipy.Policy(url=url).parse_url()

print(policy.url_meta)
```

Results:

```python
{
  'scheme': 'https',
  'domain': 'docs.github.com',
  'path': '/en/github/site-policy/github-privacy-statement',
  'params': '',
  'query': '',
  'fragment': '',
  'type': 'html'
}
```

### Policy.scrape

Obtains the page source of the given privacy policy URL. Populates the `Policy.source` attribute. Parameters:

* `timeout`: The amount of time in seconds to wait for response (default is 30).

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
policy = polipy.Policy(url=url).parse_url().scrape()

print(policy.source)
```

Results:

```html
<html lang="en"><head>

  <meta charset="utf-8">
  <title>GitHub Privacy Statement - GitHub Docs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="alternate icon" type="image/png" href="/assets/images/site/favicon.png">
  <link rel="icon" type="image/svg+xml" href="/assets/images/site/favicon.svg">
  <link rel="stylesheet" href="/dist/index.css?hash=a856c60c3b95778b47403dde9ef2fba5">
  ...
```

### Policy.extract

Extracts the text from the page source of the privacy policy. Populates the `Policy.content` attribute. Parameters:

* this method has no parameters

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
policy = polipy.Policy(url=url).parse_url().scrape().extract()

print(policy.content)
```

Results:

```python
GitHub Privacy Statement - GitHub Docs
GitHub Docs
All products
GitHub.com
Getting started
...
```

### Policy.to_dict

Retrieves the full detail of an application. Parameters:

* this method has no parameters

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
result = polipy.Policy(url=url).parse_url().scrape().extract().to_dict()

print(result)
```

Results:

```python
{
  'url': 'https://docs.github.com/en/github/site-policy/github-privacy-statement',
  'url_meta': {
    'scheme': 'https',
    'domain':
    'docs.github.com',
    'path': '/en/github/site-policy/github-privacy-statement',
    'params': '',
    'query': '',
    'fragment': '',
    'type': 'html'
  },
  'source': '...',
  'content': '...'
}
```

### get_policy

Helper method that returns a `polipy.Policy` object containing information about the policy, scraped and processed from the given URL. Parameters:


* `url`: The URL of the privacy policy.

Example:

```python
import polipy

url = 'https://docs.github.com/en/github/site-policy/github-privacy-statement'
result = polipy.get_policy(url)

print(result)
```

Results:

```python
<class 'polipy.polipy.Policy'>(
  {
    'url': 'https://docs.github.com/en/github/site-policy/github-privacy-statement',
    'url_meta': {
      'scheme': 'https',
      'domain':
      'docs.github.com',
      'path': '/en/github/site-policy/github-privacy-statement',
      'params': '',
      'query': '',
      'fragment': '',
      'type': 'html'
    },
    'source': '...',
    'content': '...'
  }
)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
