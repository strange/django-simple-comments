import datetime

from django.db import models

from simple_comments.models import BaseComment
from simple_comments import comments

class Article(models.Model):
    title = models.CharField(max_length=12)
    allow_comments = models.BooleanField(default=False)
    pub_date = models.DateTimeField(default=datetime.datetime.now())


class ArticleComment(BaseComment):
    target = models.ForeignKey(Article)


class ArticleCommentConfig(comments.CommentConfiguration):
    use_control_question = True
    allow_comments_field_name = 'allow_comments'
    autoclose_after = 25
    autoclose_after_field_name = 'pub_date'
    user_comments = True
