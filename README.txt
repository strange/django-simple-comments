======================
Django Simple Comments
======================

A generic albeit pretty flexible comments app that relies on inheritance
instead of generic relations.

I just threw this together from my old comment system. Will keep updating it
as I'm moving a lot of projects to using it.

Installation
============

At a bare minimum you need to do the following to get started.

1. Put the app in ``INSTALLED_APPS``.

2. Create a model that extends the ``BaseComment`` abstract base model. Add a
   foreign key field named ``target`` that references the model you wish to be
   able to comment on

Example::

    class ArticleComment(BaseComment):
        target = models.ForeignKey(Article)

3. Connect the comment model using a unique key.

Example::

    from simple_comments import comments
    comments.register('article', ArticleComment)

You can also create a configuration class to alter the default behaviour::

    class ArticleCommentConfiguration(CommentConfiguration):
        use_akismet = True
        target_owner_field = 'user'
        preview_template_name = 'articles/comment_preview.html'
    
    comments.register('article', ArticleComment, ArticleCommentConfiguration)

4. Hook in the generic comment URLs in your urls.py

Example::

    (
        r'^comments/', include('simple_comments.urls')
    )

TODO
====

* Test stuff.
* Add CSRF stuff.
* Add real documentation.
* Lots of ideas that'd be neat (confirm comments, comment markup option,
  confirm delete etc).
