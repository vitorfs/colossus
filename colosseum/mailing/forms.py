import csv
from io import TextIOWrapper

from django import forms
from django.utils.translation import ugettext as _

from .models import Subscriber


class NewSubscriber(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email', 'name')


class ImportSubscribersForm(forms.Form):
    upload_file = forms.FileField(help_text=_('Supported file type: .csv'))

    def import_subscribers(self, request, mailing_list_id):
        upload_file = self.cleaned_data.get('upload_file')
        csvfile = TextIOWrapper(upload_file, encoding=request.encoding)
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        subscribers = list()
        for row in reader:
            if '@' in row[0]:
                subscribers.append(
                    Subscriber(email=row[0],
                               name=row[2],
                               optin_ip_address=row[5],
                               confirm_ip_address=row[7],
                               status=Subscriber.SUBSCRIBED,
                               mailing_list_id=mailing_list_id)
                )
            else:
                continue
        Subscriber.objects.bulk_create(subscribers)

        '''
        reader = csv.reader(upload_file, delimiter=',', quotechar='"')
        next(reader)  # skip headings
        for row in reader:
            print(row)
        '''