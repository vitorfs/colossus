from collections import OrderedDict
import re

from django.template.base import VariableNode
from django.template.loader_tags import BlockNode, ExtendsNode

from bs4 import BeautifulSoup


BLOCK_RE = re.compile(r'{%\s*block\s*(\w+)\s*%}')
NAMED_BLOCK_RE = r'{%%\s*block\s*%s\s*%%}'  # Accepts string formatting
ENDBLOCK_RE = re.compile(r'{%\s*endblock\s*(?:\w+\s*)?%}')


def get_block_source(template_source, block_name):
    """
    Given a template's source code, and the name of a defined block tag,
    returns the source inside the block tag.
    """
    # Find the open block for the given name
    match = re.search(NAMED_BLOCK_RE % (block_name,), template_source)
    if match is None:
        raise ValueError('Template block %s not found' % block_name)
    end = inner_start = start = match.end()
    end_width = 0
    while True:
        # Set ``end`` current end to just out side the previous end block
        end += end_width
        # Find the next end block
        match = re.search(ENDBLOCK_RE, template_source[end:])
        # Set ``end`` to just inside the next end block
        end += match.start()
        # Get the width of the end block, in case of another iteration
        end_width = match.end() - match.start()
        # Search for any open blocks between any previously found open blocks,
        # and the current ``end``
        nested = re.search(BLOCK_RE, template_source[inner_start:end])
        if nested is None:
            # Nothing found, so we have the correct end block
            break
        else:
            # Nested open block found, so set our nested search cursor to just
            # past the inner open block that was found, and continue iteration
            inner_start += nested.end()
    # Return the value between our ``start`` and final ``end`` locations
    return template_source[start:end]


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


def get_template_blocks(template):
    nodes = template.nodelist.get_nodes_by_type(BlockNode)
    blocks = OrderedDict()
    for node in nodes:
        blocks[node.name] = get_block_source(template.source, node.name)
    return blocks


def get_plain_text_from_html(html):
    soup = BeautifulSoup(html, 'html5lib')

    for a in soup.findAll('a'):
        href = a.attrs['href']
        if a.text != href:
            link_text_repr = '%s (%s)' % (a.text, href)
        else:
            link_text_repr = href
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
