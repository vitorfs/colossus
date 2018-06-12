"""
This module is reponsible for defining the templates and the rendering
functions for the Subscriber's activities regarding their interaction with the
mailing list and emails.

Maybe not the winner of the best-engineering-solution-award, but that is what
we have for the time being.

New keys are added to the `ACTIVITIES_RENDERER` dict as needed. The key should
be the same string as defined on `Activity.activity_type` field. The value of
the dict is an anonymous function (lambda function) that takes an Activity
instance as argument (defined as `a`) and use its attributes and methods to
format the pre-defined string templates (e.g., `subscribed_template` or
`unsubscribed_template`).

Usage example:

    activity = Activity.objects.first()
    render_function = ACTIVITIES_RENDERER[activity.activity_type]
    output = render_function(activity)

The output is used in the template to list the latest activities of the
subscriber.
"""

subscribed_template = '''
<div class="jumbotron text-center mb-0">
    <i data-feather="user-plus" stroke-width="1" class="text-muted" height="64px" width="64px"></i>
    <h4>Subscribed to the List %s</h4>
    <p class="text-muted mb-0">on %s</p>
</div>'''

unsubscribed_template = '<small class="text-muted">%s</small> <strong>Unsubscribed</strong> via <a href="%s">%s</a>.'

opened_template = '<small class="text-muted">%s</small> <strong>Opened</strong> the email <a href="%s">%s</a>.'

sent_template = '<small class="text-muted">%s</small> <strong>Was sent</strong> the email <a href="%s">%s</a>.'

clicked_template = '''<small class="text-muted">%s</small> <strong>Clicked</strong>
                      <a href="%s">a link</a> in the email <a href="%s">%s</a>.'''

ACTIVITIES_RENDERER = {
    'subscribed': lambda a: subscribed_template % (
        a.subscriber.mailing_list.name,
        a.get_formatted_date()
    ),
    'unsubscribed': lambda a: unsubscribed_template % (
        a.get_formatted_date(),
        a.campaign.get_absolute_url(),
        a.campaign.name
    ),
    'sent': lambda a: sent_template % (
        a.get_formatted_date(),
        a.email.campaign.get_absolute_url(),
        a.email.campaign.name
    ),
    'opened': lambda a: opened_template % (
        a.get_formatted_date(),
        a.campaign.get_absolute_url(),
        a.campaign.name
    ),
    'clicked': lambda a: clicked_template % (
        a.get_formatted_date(),
        a.link.url,
        a.link.email.campaign.get_absolute_url(),
        a.link.email.campaign.name
    ),
}
