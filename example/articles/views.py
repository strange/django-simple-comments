from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template
from django.shortcuts import get_object_or_404

from example.articles.models import Article

def article_list(request):
    queryset = Article.objects.all()
    return object_list(request, queryset=queryset,
                       template_object_name='article',
                       template_name='articles/article_list.html')

def article_detail(request, article_id):
    context = { 'article': get_object_or_404(Article, pk=article_id) }
    return direct_to_template(request, template='articles/article_detail.html',
                              extra_context=context)
