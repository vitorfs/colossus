from django.template.base import VariableNode
from django.template.engine import Engine
from django.template.loader_tags import ExtendsNode


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
