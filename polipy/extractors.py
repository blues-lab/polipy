from bs4 import BeautifulSoup
from io import BytesIO
from pdfminer.high_level import extract_text as parse_pdf
from .exceptions import ParserException


extractors = [
    'text'
]

def extract(extractor, **kwargs):
    if extractor == 'text':
        try:
            content = extract_text(**kwargs)
        except:
            raise ParserException('Extracting Error Occurred while using the "text" extractor') from None
    # Raise Error if content is NULL
    if(len(content) == 0):
        raise ParserException('Content is Null') from None
    return content

def extract_text(url_type, url=None, dynamic_source=None, static_source=None, **kwargs):
    if url_type is None or url_type in ['html', 'other']:
        content = extract_html(dynamic_source, url)
    elif url_type == 'pdf':
        content = extract_pdf(static_source)
    elif url_type == 'plain':
        content = dynamic_source.strip()
    else:
        raise ParserException('URL Type is Unrecognized') from None
    return content

def extract_pdf(source):
    f = BytesIO(source)
    text = parse_pdf(f)
    return text.strip()

def extract_html(source, url):
    if url == 'docs.google.com' and '"s":"' in source:
        return extract_google_docs(source)
    else:
        return extract_other(source)

def extract_google_docs(source):
    chunks = source.split('"s":"')[1:]
    chunks = [x.split('"},')[0].replace('\\n', '\n').replace('\\u000b', '\n') for x in chunks]
    text = ''.join(chunks).strip()
    return text

def extract_other(source):
    """
    From https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
    """
    soup = BeautifulSoup(source, 'html.parser')

    for script in soup(['script','style']):
        script.extract()

    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split('  '))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text
