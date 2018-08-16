from .constants import TemplateKeys, Workflows

SUBSCRIPTION_FORM_TEMPLATE_SETTINGS = {

    # ==========================================================================
    # SUBSCRIBE WORKFLOW
    # ==========================================================================

    TemplateKeys.SUBSCRIBE_FORM: {
        'workflow': Workflows.SUBSCRIPTION,
        'form': 'SubscribeForm',
        'icon': 'far fa-file-alt',
        'content_template_name': 'subscribers/subscribe_form.html',
        'default_content': 'subscribers/_subscribe_form_default_content.html',
        'fields': ('content_html',),
    },
    TemplateKeys.SUBSCRIBE_THANK_YOU_PAGE: {
        'workflow': Workflows.SUBSCRIPTION,
        'icon': 'fas fa-globe',
        'content_template_name': 'subscribers/subscribe_thank_you.html',
        'default_content': 'subscribers/_subscribe_thank_you_default_content.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.CONFIRM_EMAIL: {
        'workflow': Workflows.SUBSCRIPTION,
        'icon': 'far fa-envelope',
        'content_template_name': 'subscribers/confirm_email.html',
        'default_content': 'subscribers/_confirm_email_default_content.html',
        'default_subject': 'subscribers/_confirm_email_default_subject.txt',
        'fields': ('from_name', 'from_email', 'subject', 'content_html'),
    },
    TemplateKeys.CONFIRM_THANK_YOU_PAGE: {
        'workflow': Workflows.SUBSCRIPTION,
        'icon': 'fas fa-globe',
        'content_template_name': 'subscribers/confirm_thank_you.html',
        'default_content': 'subscribers/_confirm_thank_you_default_content.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.WELCOME_EMAIL: {
        'workflow': Workflows.SUBSCRIPTION,
        'icon': 'far fa-envelope',
        'content_template_name': 'subscribers/welcome_email.html',
        'default_content': 'subscribers/_welcome_email_default_content.html',
        'default_subject': 'subscribers/_welcome_email_default_subject.txt',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    },

    # ==========================================================================
    # UNSUBSCRIBE WORKFLOW
    # ==========================================================================

    TemplateKeys.UNSUBSCRIBE_FORM: {
        'workflow': Workflows.UNSUBSCRIPTION,
        'form': 'UnsubscribeForm',
        'icon': 'far fa-file-alt',
        'content_template_name': 'subscribers/unsubscribe_form.html',
        'default_content': 'subscribers/_unsubscribe_form_default_content.html',
        'fields': ('content_html',),
    },
    TemplateKeys.UNSUBSCRIBE_SUCCESS_PAGE: {
        'workflow': Workflows.UNSUBSCRIPTION,
        'icon': 'fas fa-globe',
        'content_template_name': 'subscribers/unsubscribe_success.html',
        'default_content': 'subscribers/_unsubscribe_success_default_content.html',
        'fields': ('redirect_url', 'content_html'),
    },
    TemplateKeys.GOODBYE_EMAIL: {
        'workflow': Workflows.UNSUBSCRIPTION,
        'icon': 'far fa-envelope',
        'content_template_name': 'subscribers/goodbye_email.html',
        'default_content': 'subscribers/_goodbye_email_default_content.html',
        'default_subject': 'subscribers/_goodbye_email_default_subject.txt',
        'fields': ('send_email', 'from_name', 'from_email', 'subject', 'content_html'),
    }
}
