from .constants import TemplateKeys


SUBSCRIPTION_FORM_TEMPLATE_SETTINGS = {
    TemplateKeys.SUBSCRIBE_PAGE: {
        'template_name': 'lists/edit_subscription_form_template_page.html',
        'fields': ('content_html',),
    },
    TemplateKeys.SUBSCRIBE_THANK_YOU_PAGE: {
        'template_name': 'lists/edit_subscription_form_template_page.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.CONFIRM_EMAIL: {
        'template_name': 'lists/edit_subscription_form_template_email.html',
        'fields': ('from_name', 'from_email', 'subject', 'content_html'),
    },
    TemplateKeys.CONFIRM_THANK_YOU_PAGE: {
        'template_name': 'lists/edit_subscription_form_template_page.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.WELCOME_EMAIL: {
        'template_name': 'lists/edit_subscription_form_template_email.html',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    },
    TemplateKeys.UNSUBSCRIBE_PAGE: {
        'template_name': 'lists/edit_subscription_form_template_page.html',
        'fields': ('content_html',),
    },
    TemplateKeys.UNSUBSCRIBE_SUCCESS_PAGE: {
        'template_name': 'lists/edit_subscription_form_template_page.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.GOODBYE_EMAIL: {
        'template_name': 'lists/edit_subscription_form_template_email.html',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    }
}
