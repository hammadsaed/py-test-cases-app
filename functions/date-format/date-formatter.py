import re
from datetime import datetime


def format_date(input_text, dt_format='%Y-%m-%d'):
    convert_date = ""
    processed_date = re.sub(' +', ' ', input_text)
    processed_date = re.sub('1st', '1', processed_date)
    if re.search('1 day of', processed_date) is not None:
        processed_date = re.sub('1 day of', '1', processed_date)
    if re.search('effective ', processed_date) is not None:
        processed_date = re.sub('effective ', '', processed_date)
    if re.search('starting ', processed_date) is not None:
        processed_date = re.sub('starting ', '', processed_date)
    for fmt in (
            '%Y-%m-%d', '%d.%m.%y', '%d.%m.%Y', '%d/%m/%y', '%d/%m', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y', '%d-%m-%y',
            '%d-%m-%Y', '%d-%b-%y', '%d-%b-%Y', '%d-%B-%y', '%d-%B-%Y', '%d %m %y', '%d %m %Y', '%d %b %y', '%d %b %Y',
            '%b %d %y', '%b %d %Y', '%b.%d %Y', '%d %B %y', '%d %B %Y', '%B %Y', '%B %y', '%B %d', '%b %d', '%b y',
            '%b %Y', '%B %d %y', '%B %d %Y'):
        try:
            convert_date = datetime.strptime(processed_date, fmt).strftime(dt_format)
            if "1900" in convert_date:
                breakpoint()
                current_year = str(datetime.now().year)
                convert_date = str(convert_date).replace('1900', current_year)
        except Exception as e:
            pass
    return convert_date