from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.template.loader import get_template


def create_default_template(sender, **kwargs):
    apps = kwargs.get('apps')
    EmailTemplate = apps.get_model('templates', 'EmailTemplate')
    if not EmailTemplate.objects.exists():
        default_content = get_template('templates/default_email_template_content.html')
        content = default_content.template.source
        EmailTemplate.objects.create(name='Simple Text', content=content)


class TemplatesConfig(AppConfig):
    name = 'colossus.apps.templates'

    def ready(self):
        post_migrate.connect(create_default_template, sender=self)
