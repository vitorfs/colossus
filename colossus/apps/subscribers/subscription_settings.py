from .constants import TemplateKeys

SUBSCRIPTION_FORM_TEMPLATE_SETTINGS = {
    TemplateKeys.SUBSCRIBE_PAGE: {
        'admin_template_name': 'lists/edit_subscription_form_template_page.html',
        'content_template_name': 'subscribers/subscribe_form.html',
        'fields': ('content_html',),
    },
    TemplateKeys.SUBSCRIBE_THANK_YOU_PAGE: {
        'admin_template_name': 'lists/edit_subscription_form_template_page.html',
        'content_template_name': 'subscribers/subscribe_thank_you.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.CONFIRM_EMAIL: {
        'admin_template_name': 'lists/edit_subscription_form_template_email.html',
        'content_template_name': 'subscribers/confirm_email.txt',
        'fields': ('from_name', 'from_email', 'subject', 'content_html'),
    },
    TemplateKeys.CONFIRM_THANK_YOU_PAGE: {
        'admin_template_name': 'lists/edit_subscription_form_template_page.html',
        'content_template_name': 'subscribers/confirm_thank_you.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.WELCOME_EMAIL: {
        'admin_template_name': 'lists/edit_subscription_form_template_email.html',
        'content_template_name': 'subscribers/welcome_email.txt',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    },
    TemplateKeys.UNSUBSCRIBE_PAGE: {
        'admin_template_name': 'lists/edit_subscription_form_template_page.html',
        'content_template_name': 'subscribers/unsubscribe_form.html',
        'fields': ('content_html',),
    },
    TemplateKeys.UNSUBSCRIBE_SUCCESS_PAGE: {
        'admin_template_name': 'lists/edit_subscription_form_template_page.html',
        'content_template_name': 'subscribers/unsubscribe_success.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.GOODBYE_EMAIL: {
        'admin_template_name': 'lists/edit_subscription_form_template_email.html',
        'content_template_name': 'subscribers/goodbye_email.txt',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    }
}
