from django.conf.urls.defaults import *

p = (
    (r'^(?P<configuration_key>[\w-]+)/(?P<target_id>\d+)/post/$',
     'simple_comments.views.create_comment', {},
     'simple-comments-create-comment'),
    (r'^(?P<configuration_key>[\w-]+)/(?P<target_id>\d+)/(?P<comment_id>\d+)/delete/$',
     'simple_comments.views.delete_comment', {},
     'simple_comments_delete_comment'),
    (r'^(?P<configuration_key>[\w-]+)/(?P<target_id>\d+)/deleted/$',
     'simple_comments.views.comment_deleted', {},
     'simple_comments_comment_deleted'),
    (r'^(?P<configuration_key>[\w-]+)/$',
     'simple_comments.views.comment_list', {},
     'simple_comments_comment_list'),
    (r'^(?P<configuration_key>[\w-]+)/(?P<target_id>\d+)/$',
     'simple_comments.views.comment_list', {},
     'simple_comments_comment_list_for_target'),
    (r'^(?P<configuration_key>[\w-]+)/(?P<target_id>\d+)/(?P<comment_id>\d+)/posted/$',
     'simple_comments.views.comment_posted', {},
     'simple_comments_comment_posted'),
)

urlpatterns = patterns('', *p)
