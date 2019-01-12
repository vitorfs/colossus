from django import forms
from django.core.validators import validate_email

from colossus.apps.subscribers.models import Subscriber


class MultipleEmailField(forms.CharField):
    widget = forms.Textarea

    def clean(self, value):
        """
        First replace the commas with new lines, then split the text by lines.
        This is done so to accept both a string of emails separated by new lines
        or by commas.
        Normalize the email addresses inside a loop and call the email validator
        for each email.
        Emails are added to a dictionary so to remove the duplicates and at the
        same time preserve the case informed. The dictionary key is the lower
        case of the email, and the value is its original form.
        After the code iterates through all the emails, return only the values
        of the dictionary.
        """
        value = super().clean(value)
        emails = value.replace(',', '\n').splitlines()
        cleaned_emails = dict()
        for email in emails:
            email = Subscriber.objects.normalize_email(email)
            validate_email(email)
            cleaned_emails[email.lower()] = email
        return cleaned_emails.values()
