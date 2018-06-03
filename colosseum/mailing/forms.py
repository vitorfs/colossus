from django import forms

from .models import Subscriber


class NewSubscriber(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email', 'name')
