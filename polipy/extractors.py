from bs4 import BeautifulSoup
from io import BytesIO
from pdfminer.high_level import extract_text as parse_pdf

def extract_html(source, url):
    if url == 'docs.google.com' and '"s":"' in source:
        return extract_google_docs(source)
    else:
        return extract_text(source)

def extract_pdf(source):
    f = BytesIO(source)
    text = parse_pdf(f)
    return text.strip()

def extract_google_docs(source):
    chunks = source.split('"s":"')[1:]
    chunks = [x.split('"},')[0].replace('\\n', '\n').replace('\\u000b', '\n') for x in chunks]
    text = ''.join(chunks).strip()
    return text

def extract_text(source):
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
