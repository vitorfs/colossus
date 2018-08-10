from datetime import datetime

import pytz


def convert_date(str_date: str) -> datetime:
    date = datetime.strptime(str_date.strip(), '%Y-%m-%d %H:%M:%S')
    return pytz.utc.localize(date)


def normalize_email(email: str) -> str:
    from colossus.apps.subscribers.models import Subscriber
    return Subscriber.objects.normalize_email(email)


def normalize_text(text: str) -> str:
    if text is None:
        return ''
    text = str(text)
    text = ' '.join(text.split())
    return text
