from django.shortcuts import get_object_or_404
from django.views.generic.base import ContextMixin

from .models import MailingList


class MailingListMixin(ContextMixin):
    __mailing_list = None

    @property
    def mailing_list(self):
        if self.__mailing_list is None:
            self.__mailing_list = get_object_or_404(MailingList, pk=self.kwargs.get('pk'))
        return self.__mailing_list

    def get_context_data(self, **kwargs):
        if 'menu' not in kwargs:
            kwargs['menu'] = 'lists'
        if 'mailing_list' not in kwargs:
            kwargs['mailing_list'] = self.mailing_list
        return super().get_context_data(**kwargs)
