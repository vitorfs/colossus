from django.template.base import VariableNode
from django.template.engine import Engine
from django.template.loader_tags import ExtendsNode

from bs4 import BeautifulSoup


def _get_template_variables(template):
    """
    Extracts all the variable node tokens of the given template.
    This gets worked out recursively by extracting nodes from possible
    parent templates via the extension nodes.
    """
    var_nodes = template.nodelist.get_nodes_by_type(VariableNode)
    template_vars = [_v.filter_expression.token for _v in var_nodes]

    for ext_node in template.nodelist.get_nodes_by_type(ExtendsNode):
        template_vars += _get_template_variables(
            ext_node.get_parent(ext_node.parent_name))

    return template_vars


def get_template_variables(template):
    """
    Returns unique variable names found in the given template and its parents.
    This will ignore "block" variables.
    """
    clean_variables = filter(lambda _v: not _v.startswith('block'), _get_template_variables(template))
    return set(clean_variables)


def get_plain_text_from_html(html):
    soup = BeautifulSoup(html, 'html5lib')

    for a in soup.findAll('a'):
        link_text_repr = '%s (%s)' % (a.text, a.attrs['href'])
        a.replaceWith(link_text_repr)

    for li in soup.findAll('li'):
        list_text_repr = '* %s' % (li.text)
        li.replaceWith(list_text_repr)

    for strong in soup.findAll('strong'):
        strong_text_repr = '*%s*' % (strong.text)
        strong.replaceWith(strong_text_repr)

    for b in soup.findAll('b'):
        bold_text_repr = '*%s*' % (b.text)
        b.replaceWith(bold_text_repr)

    for em in soup.findAll('em'):
        emphasis_text_repr = '_%s_' % (em.text)
        em.replaceWith(emphasis_text_repr)

    for i in soup.findAll('i'):
        italic_text_repr = '_%s_' % (i.text)
        i.replaceWith(italic_text_repr)

    return soup.text
