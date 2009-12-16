tests = """
>>> user = User.objects.create_user(username=u'x', email=u'x@x.com')

>>> article = Article(title=u'test')
>>> article.save()

>>> c1 = ArticleComment(target=article, user=user)
>>> c1.save()
>>> c1.author_name
u'x'
>>> c1.author_email
u'x@x.com'

>>> user.first_name = u'f'
>>> user.last_name = u'l'
>>> user.save()

>>> c2 = ArticleComment(target=article, user=user)
>>> c2.save()
>>> c2.author_name
u'f l'

# >>> form = EarTriviaForm(data={ 'question': EarTriviaForm.CORRECT_ANSWER })
# >>> form.is_valid()
# True

# config tests

>>> b = ArticleCommentConfig('test', ArticleComment)

>>> form = b.get_form()()
>>> print form.as_p()
<p><label for="id_author_name">Author name:</label> <input id="id_author_name" type="text" name="author_name" maxlength="61" /></p>
<p><label for="id_author_email">Author email:</label> <input id="id_author_email" type="text" name="author_email" maxlength="75" /></p>
<p><label for="id_author_website">Author website:</label> <input id="id_author_website" type="text" name="author_website" maxlength="200" /></p>
<p><label for="id_body">Body:</label> <textarea id="id_body" rows="10" cols="40" name="body"></textarea></p>

# Test if comments are allowed. The first case should evaluate to False as 
# the allow comments field on the article evaluates to False at this point.
>>> b.allow_comments(article)
False

# So we allow comments on the article.
>>> article.allow_comments = True
>>> article.save()
>>> b.allow_comments(article)
True

# They shouldn't be allowed now as we make the article 30 days old.
>>> article.pub_date = datetime.datetime.now() - datetime.timedelta(days=30)
>>> article.save()
>>> b.allow_comments(article)
False

# We're relying on the ForeignKey to determine the model we're attaching
# comments to.
>>> ArticleComment.get_target_model()
<class 'example.articles.models.Article'>

>>> comments.register('article', ArticleComment, ArticleCommentConfig)
>>> comments.get_configuration('article').__class__
<class 'example.articles.models.ArticleCommentConfig'>
"""

import datetime

from django import forms
from django.db import models
from django.contrib.auth.models import User

from simple_comments.forms import EarTriviaForm
from simple_comments import comments

from example.articles.models import Article
from example.articles.models import ArticleComment
from example.articles.models import ArticleCommentConfig

__test__ = { 'doctest': tests }
