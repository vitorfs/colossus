from .constants import ActivityTypes

SUBSCRIBED_TEMPLATE = '''
<div class="jumbotron text-center mb-0">
    <i data-feather="user-plus" stroke-width="1" class="text-muted" height="64px" width="64px"></i>
    <h4>Subscribed to the List %s</h4>
    <p class="text-muted mb-0">on %s</p>
</div>'''

UNSUBSCRIBED_TEMPLATE = '<small class="text-muted">%s</small> <strong>Unsubscribed</strong>.'

UNSUBSCRIBED_CAMPAIGN_TEMPLATE = '''<small class="text-muted">%s</small>
                                    <strong>Unsubscribed</strong> via <a href="%s">%s</a>.'''

OPENED_TEMPLATE = '<small class="text-muted">%s</small> <strong>Opened</strong> the email <a href="%s">%s</a>.'

SENT_TEMPLATE = '<small class="text-muted">%s</small> <strong>Was sent</strong> the email <a href="%s">%s</a>.'

CLICKED_TEMPLATE = '''<small class="text-muted">%s</small> <strong>Clicked</strong>
                      <a href="%s">a link</a> in the email <a href="%s">%s</a>.'''

IMPORTED_TEMPLATE = '<small class="text-muted">%s</small> <strong>Imported</strong> to the List %s'

CLEANED_TEMPLATE = '<small class="text-muted">%s</small> <strong>Cleaned</strong> from the List.'


def render_unsubscribe_activity(activity):
    if activity.campaign is not None:
        return UNSUBSCRIBED_CAMPAIGN_TEMPLATE % (activity.get_formatted_date(),
                                                 activity.campaign.get_absolute_url(),
                                                 activity.campaign.name)
    else:
        return UNSUBSCRIBED_TEMPLATE % activity.get_formatted_date()


def render_activity(activity):
    """
    This module is responsible for defining the templates and the rendering
    functions for the Subscriber's activities regarding their interaction with the
    mailing list and emails.

    Maybe not the winner of the best-engineering-solution-award, but that is what
    we have for the time being.

    New keys are added to the `renderers` dict as needed. The key should
    be the same string as defined on `Activity.activity_type` field. The value of
    the dict is an anonymous function (lambda function) that takes an Activity
    instance as argument (defined as `a`) and use its attributes and methods to
    format the pre-defined string templates (e.g., `SUBSCRIBED_TEMPLATE` or
    `UNSUBSCRIBED_TEMPLATE`).

    The `html` output is used in the template to list the latest activities of the
    subscriber.
    """
    renderers = {
        ActivityTypes.SUBSCRIBED: lambda a: SUBSCRIBED_TEMPLATE % (
            a.subscriber.mailing_list.name,
            a.get_formatted_date()
        ),
        ActivityTypes.UNSUBSCRIBED: render_unsubscribe_activity,
        ActivityTypes.SENT: lambda a: SENT_TEMPLATE % (
            a.get_formatted_date(),
            a.email.campaign.get_absolute_url(),
            a.email.campaign.name
        ),
        ActivityTypes.OPENED: lambda a: OPENED_TEMPLATE % (
            a.get_formatted_date(),
            a.email.campaign.get_absolute_url(),
            a.email.campaign.name
        ),
        ActivityTypes.CLICKED: lambda a: CLICKED_TEMPLATE % (
            a.get_formatted_date(),
            a.link.url,
            a.link.email.campaign.get_absolute_url(),
            a.link.email.campaign.name
        ),
        ActivityTypes.IMPORTED: lambda a: IMPORTED_TEMPLATE % (
            a.get_formatted_date(),
            a.subscriber.mailing_list.name,
        ),
        ActivityTypes.CLEANED: lambda a: CLEANED_TEMPLATE % a.get_formatted_date()
    }
    renderer = renderers[activity.activity_type]
    html = renderer(activity)
    return html
