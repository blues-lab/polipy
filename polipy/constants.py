import os, datetime

UTC_DATE = datetime.datetime.utcnow().strftime('%Y%m%d')
CWD = os.getcwd()

KEYWORDS = {
    'identifiers': [
        'real name', 'alias', 'postal address', 'address', 'unique personal identifier',
        'online identifier', 'IP address', 'email address', 'email', 'account name',
        'social security number', 'driver license number', 'passport number'
    ],
    'customer records information': [
        'name', 'signature', 'social security number', 'ssn',
        'physical characteristics', 'address', 'telephone number', 'phone number',
        'passport number', 'drivers license',
        'state identification card number', 'insurance policy number',
        'education', 'employment', 'employment history', 'bank account number',
        'credit card number', 'debit card number', 'financial information',
        'medical information', 'health insurance information'
    ]
}
