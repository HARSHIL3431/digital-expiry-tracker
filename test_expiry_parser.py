from app.services.expiry_parser import ExpiryParser

parser = ExpiryParser()

samples = [
    "EXP: 10/06/2025",
    "Best before Aug 2025",
    "Use before 12-09-25",
]

for s in samples:
    print(s, "=>", parser.extract_expiry_date(s))
