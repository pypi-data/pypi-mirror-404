import re

class Regexs(object):

    DATA01 = r"^((?:https?:)?\/\/)"
    DATA02 = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"
    DATA03 = r"^https://www\.instagram\.com/([A-Za-z0-9._]+/)?(p|tv|reel)/([A-Za-z0-9\-_]*)"
    DATA10 = r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"

    DATA11 = r'\s+'
    DATA12 = r'[_-]'
    DATA13 = r'[@_-]'
    DATA14 = rf'[^\w\s\u0B80-\u0BFF\u0D00-\u0D7F]'

    DATA21 = re.compile(r'([@#])(?=\w+)')
    DATA22 = re.compile(r'https?://\S+', re.IGNORECASE)

    DATA31 = r'@\w+'                                     # usernames
    DATA32 = r'www\.\S+'                                 # www links
    DATA33 = r't\.me/\S+'                                # telegram links
    DATA34 = r'https?://\S+'                             # http links
    DATA35 = r'\b(channel|group|telegram)\b.*'           # channel spam
    DATA36 = r'\b(join|subscribe|follow|share)\b.*'      # promo words
    DATA37 = r'\b(upload|uploaded|download|channel)\b.*' # promo words
    DATA38 = r'[|~=_]{2,}'
    DATA39 = r'[^a-zA-Z0-9 .,!?()-]'
