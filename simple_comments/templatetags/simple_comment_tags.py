from django import template

from simple_comments import comments

register = template.Library()

# Filters

@register.filter
def has_permission_to_delete(user, comment, configuration):
    return configuration.has_permission_to_delete(comment, user)

@register.filter
def allow_post_for_user(config, user):
    return not config.user_comments or user.is_authenticated()

@register.filter
def allow_comments(config, target):
    return config.allow_comments(target)

# Nodes

class ContextInsertingNode(template.Node):
    """Convenience class used to create nodes handling insertion of
    stuff into context.
    
    """
    def __init__(self, configuration_key, target, context_variable_name):
        self.configuration_key = template.Variable(configuration_key)
        self.target = template.Variable(target)
        self.context_variable_name = template.Variable(context_variable_name)

    def render(self, context):
        configuration_key = self.configuration_key.resolve(context)
        configuration = comments.get_configuration(configuration_key)
        data = self.get_data(context, configuration,
                             self.target.resolve(context))
        context[self.context_variable_name.resolve(context)] = data
        return ''

    def get_data(self, configuration, target):
        raise NotImplementedError


class CommentListNode(ContextInsertingNode):
    def get_data(self, context, configuration, target):
        queryset = configuration.model._default_manager.filter(target=target)
        queryset = queryset.order_by(configuration.order_by)
        return queryset


class CommentFormNode(ContextInsertingNode):
    def get_data(self, context, configuration, target):
        return configuration.get_form()()


class CommentSpamFormsNode(ContextInsertingNode):
    def get_data(self, context, configuration, target):
        return [f(request=None) for \
                f in configuration.get_spam_prevention_forms()]


class ConfigurationNode(ContextInsertingNode):
    def get_data(self, context, configuration, target):
        return configuration

# Register tags

@register.tag('comment_form')
def do_comment_form(parser, token):
    """Insert a form for ``configuration`` into context.

    Example::
        {% comment_form for 'configuration_key' article as 'form' %}

    """
    bits = split_tokens(token)
    return CommentFormNode(bits[2], bits[3], bits[5])

@register.tag('comment_spam_forms')
def do_comment_spam_forms(parser, token):
    """Insert spam forms for ``configuration`` into context.

    Example::
        {% comment_form for 'configuration_key' article as 'form' %}

    """
    bits = split_tokens(token)
    return CommentSpamFormsNode(bits[2], bits[3], bits[5])

@register.tag('comment_list')
def do_comment_list(parser, token):
    """Insert list of comments for target matching ``target_id`` into context.

    Example::
        {% comment_list for 'configuration_key' article as 'comment_list' %}

    """
    bits = split_tokens(token)
    return CommentListNode(bits[2], bits[3], bits[5])

@register.tag('comment_configuration')
def do_comment_configuration(parser, token):
    """Insert configuration matching `configuration_key` into context.

    Example::
        {% comment_configuration for 'configuration_key' article as 'configuration' %}

    """
    bits = split_tokens(token)
    return ConfigurationNode(bits[2], bits[3], bits[5])

def split_tokens(token):
    bits = token.contents.split()
    if len(bits) != 6:
        raise template.TemplateSyntaxError("'%s' tag takes five arguments" % bits[0])
    if bits[1] != 'for':
        raise template.TemplateSyntaxError("First argument to %r tag must be 'for'" % tokens[0])
    if bits[4] != 'as':
        raise template.TemplateSyntaxError("Fourth argument to '%s' tag must be 'as'" % bits[0])
    return bits
