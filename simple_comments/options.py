import datetime

from django.conf import settings
from django.forms.models import modelform_factory
from simple_comments import forms as comment_forms

NOTIFICATION_LABEL = 'simple_comments_comment'

class BaseCommentConfiguration(object):
    """A set of basic configuration options for handling comments. Subclass
    this class to create your own custom behaviour.
    
    There are three builtin levels of spam prevention: ``use_akismet``,
    ``use_control_question`` and ``use_honeypot`` are all boolean attributes
    that allows enabling of spam prevention. Override
    ``get_spam_prevention_form`` in a subclass to add custom spam prevention
    mechanisms.
    
    You can add support for your own spam prevention mechanisms by overriding
    ``get_spam_prevention_form()`` (and adding your own custom attribute(s)
    to decide what mechanism to use if you want to retain the ability to use
    the standard ones).
    
    ``user_comments`` determines whether a user must be registered in order to
    post comments. It will also remove the need for a poster to fill in
    otherwise mandatory fields such as name and email.
    
    ``user_can_delete`` determines if users should be able to delete their own
    comments or not.
    
    ``autoclose_after`` is the number of days after when comments should be
    automatically closed for a target. ``autoclose_field`` is the name of a
    date/datetime field on the target model used when determining if comments
    should be closed.
    
    ``allow_comments_field`` is a boolean field on the target model that, when
    evaluating to ``False`` prevents comments from being posted.

    Methods:

    ``get_target_owner`` return the owner of the target. Used to determine if a
    user can delete a comment or not.
    
    """
    use_akismet = False
    use_control_question = False
    use_honeypot = False
    
    user_comments = False
    user_can_delete = False
    
    autoclose_after = None
    autoclose_field = None
    
    prevent_duplicates = True
    
    allow_comments_field = None
    
    preview_template_name = 'simple_comments/comment_preview.html'
    form_template_name = 'simple_comments/comment_form.html'
    list_template_name = 'simple_comments/comment_list.html'
    
    send_notifications = False

    order_by = 'pub_date'
    paginate_by = 25
    
    def get_exclude(self):
        """Return a list of fields to exclude when generating a form using
        ``get_form()``. Defaults to the basic fields of the ``BaseComment`` we
        want to exclude. Subclasses may override this method to alter the list
        of fields to exlcude, albeit it's probably easier to just set the
        ``exclude`` attribute.
        
        """
        exclude = ['user', 'user_username', 'pub_date', 'ip_address', 'target']
        if self.user_comments:
            exclude += ['author_name', 'author_email', 'author_website']
        return exclude
    exclude = property(fget=lambda self: self.get_exclude())
    
    def _days_since_published(self, target):
        """Return the number of days that have passed since ``target`` was
        published.
        
        """
        now = datetime.datetime.now()
        published = getattr(target, self.autoclose_field)
        return datetime.date(now.year, now.month, now.day) - \
               datetime.date(published.year, published.month, published.day)
    
    def allow_comments(self, target):
        """Return a boolean dictating whether comments are allowed for
        ``target`` or not.
        
        """
        if self.allow_comments_field is not None and \
           not getattr(target, self.allow_comments_field):
            return False

        if self.autoclose_field is not None and self.autoclose_after is not None:
            return self._days_since_published(target).days < self.autoclose_after
        return True

    def get_form(self, comment_model, do_not_use_spam_prevention=False):
        """Return a form for use when creating comments.
        
        If any measures against spam are to be taken, and
        ``do_not_use_spam_prevention`` does not evaluate to ``True``, a spam
        prevention form extending the default model form will be returned.
        
        """
        model_form = self.get_model_form(comment_model)
        spam_form = self.get_spam_prevention_form(model_form)
        if spam_form is None or do_not_use_spam_prevention:
            return model_form
        return spam_form
    
    def get_model_form(self, comment_model):
        """Return a ``ModelForm`` for ``comment_model``. Subclasses can
        override this method to return a custom base form the will be
        subclassed by "spam forms" if applicable.
        
        """
        return modelform_factory(comment_model, fields=None,
                                 exclude=self.exclude)

    def get_spam_prevention_form(self, model_form):
        """Return a spam prevention form if settings dictate that one is to
        be used. Otherwise return ``None``.
        
        """
        if self.use_akismet:
            return comment_forms.akismet_form_factory(model_form)
        if self.use_control_question:
            return comment_forms.ear_trivia_form_factory(model_form)
        if self.use_honeypot:
            return comment_forms.honeypot_form_factory(model_form)
        return None
    
    def has_permission_to_delete(self, comment, user, request=None):
        """Return a boolean dictating whether a user has permission to delete
        a comment or not.
        
        """
        if user is None or user.is_anonymous():
            return False

        target_owner = self.get_target_owner(comment.target)
        if self.user_can_delete and \
           (comment.user == user or target_owner == user):
            return True

        if request is not None:
            opts = comment.target._meta
            perm = '%s.%s' % (opts.app_label, opts.get_delete_permission())
            if request.user.has_perm(perm):
                return True
        return False

    def get_target_owner(self, target):
        """Return the owner (``User`` instance) of target."""
        return None
    
    def get_duplicate(self, target, comment):
        """Try to determine if duplicate posts exist. If posts made by the same
        author, with the same content exists for the same day the latest
        "duplicate" record is returned. Otherwise return ``None``.

        This method should be overridden if a custom model (that requires
        custom checks) is used.
        
        """
        filter_kwargs = {
            'user': comment.user,
            'author_name': comment.author_name,
            'author_email': comment.author_email,
            'author_website': comment.author_website,
            'target': target,
        }
        queryset = comment._default_manager.filter(**filter_kwargs)
        queryset = queryset.order_by('-pub_date')
        if queryset.count():
            latest = queryset[0]
            if latest.pub_date.date() == comment.pub_date.date() and \
               latest.body == comment.body:
                return latest
        return None
    
    def get_post_save_redirect_url(self, target, comment):
        """Return a URL to redirect to after a successful comment save."""
        return "%s#comment-%s" % (target.get_absolute_url(), comment.id)
            
    def get_post_delete_redirect_url(self, target):
        """Return a URL to redirect to after a successful comment delete."""
        return target.get_absolute_url()

    def get_notification_users(self, target):
        """Return an iterable of ``User`` instances that should be notified
        when a comment is made on ``target``.
        
        """
        return [self.get_target_owner(target)]

    def send_notification(self, comment):
        users = self.get_notification_users(comment.target)
        if not self.send_notifications or \
           "notification" not in settings.INSTALLED_APPS or not users:
            return False

        from notification import models as notification
        context = {
            'comment': comment,
            'verbose_name': comment.target._meta.verbose_name,
        }
        notification.send(users, NOTIFICATION_LABEL, context)
        return True


class CommentOptionAlreadyRegistered(Exception):
    pass


class CommentOptionNotRegistered(Exception):
    pass


class CommentOptions(object):
    """Register comment models and configurations."""
    
    __shared_state = {
        'configurations': {},
        'models': {}
    }
    
    def __init__(self):
        self.__dict__ = self.__shared_state
    
    def register(self, option_key, comment_model,
                 configuration_class=BaseCommentConfiguration):
        """Register ``comment_model`` and ``configuration_class`` against
        ``option_key``. If configuration class is not given the default
        ``BaseCommentConfiguration`` will be used.
        
        """
        try:
            self.configurations[option_key]
            raise CommentOptionAlreadyRegistered
        except KeyError:
            self.configurations[option_key] = (comment_model,
                                               configuration_class)
    
    def unregister(self, option_key):
        """Unregister model and configuration matching ``option_key``."""
        try:
            del(self.configurations[option_key])
        except KeyError:
            raise CommentOptionNotRegistered
    
    def get_model_and_configuration(self, option_key):
        """Return the comment model and configuration associated with
        ``option_key``.
        
        """
        try:
            return self.configurations[option_key]
        except KeyError:
            raise CommentOptionNotRegistered


options = CommentOptions()

register = options.register
unregister = options.unregister
get_model_and_configuration = options.get_model_and_configuration
