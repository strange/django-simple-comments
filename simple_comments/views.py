from django import http

from simple_comments import comments

def get_configuration_or_404(configuration_key):
    try:
        return comments.get_configuration(configuration_key)
    except comments.CommentConfigurationNotRegistered:
        raise http.Http404

def create_comment(request, configuration_key, target_id, extra_context=None):
    config = get_configuration_or_404(configuration_key)
    return config.create_comment(request, target_id, extra_context)

def comment_posted(request, configuration_key, target_id, comment_id,
                   extra_context=None):
    config = get_configuration_or_404(configuration_key)
    return config.comment_posted(request, target_id, comment_id,
                                  extra_context)


def delete_comment(request, configuration_key, target_id, comment_id):
    config = get_configuration_or_404(configuration_key)
    return config.delete_comment(request, target_id, comment_id)

def comment_deleted(request, configuration_key, target_id,
                    extra_context=None):
    config = get_configuration_or_404(configuration_key)
    return config.comment_deleted(request, target_id, comment_id,
                                  extra_context)

def comment_list(request, configuration_key, target_id=None,
                 extra_context=None):
    config = get_configuration_or_404(configuration_key)
    return config.comment_list(request, target_id, extra_context)
