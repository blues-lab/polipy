import os, datetime

UTC_DATE = datetime.datetime.utcnow().strftime('%Y%m%d')
CWD = os.getcwd()

KEYWORDS = {
    'identifiers': [
        'real name', 'alias', 'postal address', 'address',
        'unique personal identifier', 'online identifier', 'IP address',
        'email address', 'email', 'account name', 'social security number',
        'driver license number', 'passport number'
    ],
    'customer records information': [
        'name', 'signature', 'social security number', 'ssn',
        'physical characteristics', 'address', 'telephone number',
        'phone number', 'passport number', 'drivers license',
        'state identification card number', 'insurance policy number',
        'education', 'employment', 'employment history', 'bank account number',
        'credit card number', 'debit card number', 'financial information',
        'medical information', 'health insurance information'
    ],
    'characteristics of protected classifications': [
        'race', 'ancestry', 'national origin', 'religion', 'age',
        'mental and physical disability', 'sex', 'sexual orientation',
        'gender identity', 'medical condition', 'genetic information',
        'marital status', 'military status'
    ],
    'commercial information': [
        'personal property', 'products purchased', 'services purchased',
        'purchasing histories', 'consuming histories'
    ],
    'internet or other electronic network activity information': [
        'browsing history', 'search history',
        'interaction with a website, application, or advertisement'
    ],
    'geolocation data': ['geolocation data', 'location information', 'gps'],
    'sensory data': ['Audio', 'electronic', 'visual', 'thermal', 'olfactory'],
    'professional or employment-related information':
    ['employment information', 'professional information'],
    'education information':
    ['Family Educational Rights and Privacy Act', 'education', 'school'],
    'inferences': [
        'psychological trends', 'predispositions', 'behavior', 'attitudes',
        'intelligence', 'aptitude'
    ]
}
