subscribed_template = '''
<div class="jumbotron text-center mb-0">
    <i data-feather="user-plus" stroke-width="1" class="text-muted" height="64px" width="64px"></i>
    <h4>Subscribed to the List %s</h4>
    <p class="text-muted mb-0">on %s</p>
</div>'''

unsubscribed_template = '<small class="text-muted">%s</small> <strong>Unsubscribed</strong> via <a href="%s">%s</a>.'

opened_template = '<small class="text-muted">%s</small> <strong>Opened</strong> the email <a href="%s">%s</a>.'

sent_template = '<small class="text-muted">%s</small> <strong>Was sent</strong> the email <a href="%s">%s</a>.'

clicked_template = '<small class="text-muted">%s</small> <strong>Clicked</strong> <a href="%s">a link</a> in the email <a href="%s">%s</a>.'

ACTIVITIES_RENDERER = {
    'subscribed': lambda a: subscribed_template % (a.subscriber.mailing_list.name, a.get_formatted_date()),
    'unsubscribed': lambda a: unsubscribed_template % (a.get_formatted_date(), a.campaign.get_absolute_url(), a.campaign.name),
    'sent': lambda a: sent_template % (a.get_formatted_date(), a.email.campaign.get_absolute_url(), a.email.campaign.name),
    'opened': lambda a: opened_template % (a.get_formatted_date(), a.campaign.get_absolute_url(), a.campaign.name),
    'clicked': lambda a: opened_template % (a.get_formatted_date(), a.link.url, a.campaign.get_absolute_url(), a.campaign.name),
}
