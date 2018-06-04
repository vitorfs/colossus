from django import forms

from colossus.mailing.models import Subscriber


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email',)

    def save(self, commit=True):
        subscriber = super().save(commit=False)
        if commit:
            subscriber.save()
        return subscriber
