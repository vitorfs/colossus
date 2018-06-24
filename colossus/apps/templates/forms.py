from django import forms
from django.core.exceptions import ValidationError
from django.template import Template, TemplateSyntaxError
from django.template.loader_tags import ExtendsNode, IncludeNode
from django.utils import timezone
from django.utils.translation import gettext

from .models import EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ('content',)

    def clean_content(self):
        content = self.cleaned_data.get('content')

        try:
            template = Template(content)

            if template.nodelist.get_nodes_by_type(IncludeNode):
                include_tag_not_allowed = ValidationError(
                    gettext('Include blocks are not allowed.'),
                    code='include_tag_not_allowed'
                )
                self.add_error('content', include_tag_not_allowed)

            if template.nodelist.get_nodes_by_type(ExtendsNode):
                extends_tag_not_allowed = ValidationError(
                    gettext('Extends blocks are not allowed.'),
                    code='extends_tag_not_allowed'
                )
                self.add_error('content', extends_tag_not_allowed)

        except TemplateSyntaxError as tse:
            template_syntax_error = ValidationError(str(tse), code='template_syntax_error')
            self.add_error('content', template_syntax_error)

        return content

    def save(self, commit=True):
        email_template = super().save(commit=False)
        email_template.update_date = timezone.now()
        if commit:
            email_template.save()
        return email_template
