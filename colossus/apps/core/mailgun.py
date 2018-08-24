from django.conf import settings

import requests


class Mailgun:
    def _request(self, method: str, endpoint: str):
        url = '%s/%s' % (settings.MAILGUN_API_BASE_URL, endpoint)
        response = requests.request(method, url, auth=('api', settings.MAILGUN_API_KEY))
        return response

    def bounces(self):
        response = self._request('get', 'bounces')
        return response.json()

    def delete_bounce(self, address: str):
        endpoint = 'bounces/%s' % address
        response = self._request('delete', endpoint)
        return response.json()
