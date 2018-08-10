import datetime
from collections import OrderedDict

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from colossus.apps.subscribers.constants import ActivityTypes
from colossus.apps.subscribers.models import Activity


class Chart:
    def __init__(self, chart_type):
        self._chart_type = chart_type

    def get_chart_type(self):
        return self._chart_type

    def get_data(self):
        raise NotImplementedError

    def get_options(self):
        raise NotImplementedError

    def get_settings(self):
        settings = {
            'type': self.get_chart_type(),
            'data': self.get_data(),
            'options': self.get_options()
        }
        return settings


class SubscriptionsSummaryChart(Chart):
    """
    Build the last 30 days subscriptions summary in the list summary page.
    Solid blue line display number of subscriptions, dashed red line shows
    number of unsubscriptions.
    """
    def __init__(self, mailing_list):
        super().__init__(chart_type='bar')
        self.mailing_list = mailing_list

    def get_data(self):
        thirty_days_ago = timezone.now() - datetime.timedelta(30)

        # Group by query returning the counts for subscribe actions and
        # unsubscribe actions. The Count queries are defined externally
        # for readability.
        # Output format:
        # <QuerySet [
        #     {'trunc_date': datetime.date(2018, 6, 10), 'subscribed': 1, 'unsubscribed': 0},
        #     {'trunc_date': datetime.date(2018, 6, 11), 'subscribed': 3, 'unsubscribed': 2},
        #     {'trunc_date': datetime.date(2018, 6, 12), 'subscribed': 1, 'unsubscribed': 0}
        # ]>
        subscribed_expression = Count('id', filter=Q(activity_type=ActivityTypes.SUBSCRIBED))
        unsubscribed_expression = Count('id', filter=Q(activity_type=ActivityTypes.UNSUBSCRIBED))
        activities = Activity.objects \
            .filter(subscriber__mailing_list=self.mailing_list, date__gte=thirty_days_ago) \
            .values(trunc_date=TruncDate('date')) \
            .annotate(subscribed=subscribed_expression, unsubscribed=unsubscribed_expression) \
            .order_by('trunc_date')

        # First initialize the `series` dictionary with all last 30 days.
        # This is necessary because if the count of subscribers for a given
        # day is equal to zero (or if the queryset is empty all together)
        # we can still show an empty bar in the bar chart for that day.
        # It's a way to keep the rendering of the bar chart consistent.
        series = OrderedDict()
        for i in range(-1, 29):  # FIXME: There is an issue with current day, or something related to timezone
            date = timezone.now() - datetime.timedelta(i)
            key = date.strftime('%-d %b, %y')
            series[key] = {'sub': 0, 'unsub': 0, 'order': i}

        # Now we are replacing the existing entries with actual counts
        # comming from our queryset.
        for entry in activities:
            key = entry['trunc_date'].strftime('%-d %b, %y')
            series[key]['sub'] = entry['subscribed']
            series[key]['unsub'] = entry['unsubscribed']

        # Here is time to grab the info and place on lists for labels
        # and the data. Note that we are sorting the series data so to
        # display from the oldest day to the most recent.
        labels = list()
        subscriptions = list()
        unsubscriptions = list()
        for key, value in sorted(series.items(), key=lambda e: e[1]['order'], reverse=True):
            labels.append(key)
            subscriptions.append(value['sub'])
            unsubscriptions.append(value['unsub'])
        data = {
            'labels': labels,
            'datasets': [
                {
                    'label': _('Unsubscritions'),
                    'borderColor': '#f25b69',
                    'backgroundColor': 'transparent',
                    'data': unsubscriptions,
                    'type': 'line',
                    'borderDash': [10, 5]
                },
                {
                    'label': _('Subscriptions'),
                    'borderColor': '#3a99fc',
                    'backgroundColor': '#3a99fc',
                    'data': subscriptions
                }
            ]
        }
        return data

    def get_options(self):
        options = {
            'scales': {
                'yAxes': [{
                    'ticks': {
                        'beginAtZero': True
                    }
                }]
            }
        }
        return options
