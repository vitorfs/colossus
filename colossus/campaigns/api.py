from smtplib import SMTPException

from django.core.mail import send_mail, EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils.translation import gettext as _


def get_test_email_context():
    context = {
        'name': '<< Test Name >>',
        'unsub': '#'
    }
    return context


def send_campaign_email(email, context, to, is_test=False):
    if isinstance(to, str):
        to = [to,]

    if is_test:
        subject = '[%s] %s' % (_('Test'), email.subject)
    else:
        subject = email.subject

    plain_text_message = email.render_text(context)
    rich_text_message = email.render_html(context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=plain_text_message,
        from_email=email.get_from(),
        to=to,
    )
    message.attach_alternative(rich_text_message, 'text/html')

    try:
        message.send(fail_silently=False)
        return True
    except SMTPException as err:
        # TODO: log error message
        return False


def send_campaign_email_subscriber(email, subscriber):
    context = {
        'name': subscriber.name,
        'unsub': reverse('subscribers:unsubscribe', kwargs={
            'mailing_list_uuid': email.campaign.mailing_list.uuid,
            'subscriber_uuid': subscriber.uuid,
            'campaign_uuid': email.campaign.uuid
        })
    }
    return send_campaign_email(email, context, subscriber.get_email())


def send_campaign_email_test(email, recipient_list):
    context = get_test_email_context()
    return send_campaign_email(email, context, recipient_list, is_test=True)


def send_campaign(campaign):
    with get_connection() as connection:
        for subscriber in campaign.mailing_list.get_active_subscribers():
            sent = send_campaign_email_subscriber(campaign.email, subscriber)
            if sent:
                subscriber.create_activity('sent', email=campaign.email)
