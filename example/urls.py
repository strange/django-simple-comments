from django.conf.urls.defaults import *
from django.contrib import admin

from simple_comments import comments

from example.articles.models import ArticleComment
from example.articles.models import ArticleCommentConfig

comments.register('articles', ArticleComment, ArticleCommentConfig)
admin.autodiscover()

p = (
    (r'^admin/', include(admin.site.urls)),
    (r'^comments/', include('simple_comments.urls')),
    (r'^articles/$', 'example.articles.views.article_list', {}, 'article-list'),
    (r'^articles/(?P<article_id>\d+)/$',
     'example.articles.views.article_detail', {}, 'article-detail'),
)

urlpatterns = patterns('', *p)
