import datetime

from django import http
from django.conf import settings
from django.forms.models import modelform_factory
from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse

from simple_comments import forms as comment_forms

NOTIFICATION_LABEL = 'simple_comments_comment'

class CommentConfiguration(object):
    """A set of basic configuration options for handling comments. Subclass
    this class to create your own custom behaviour.
    
    There are three builtin levels of spam prevention: ``use_akismet``,
    ``use_control_question`` and ``use_honeypot`` are all boolean attributes
    that allows enabling of spam prevention. Override
    ``get_spam_prevention_forms`` in a subclass to add custom spam prevention
    mechanisms.
    
    ``user_comments`` determines whether a user must be registered in order to
    post comments. It will also remove the need for a poster to fill in
    otherwise mandatory fields such as name and email.
    
    ``user_can_delete`` determines if users should be able to delete their own
    comments or not.
    
    ``autoclose_after`` determines how many days should pass after the target
    was created before comments should be closed.  ``autoclose_field_name`` is
    the name of a date/datetime field on the target model that specifies when
    the target was created.

    ``prevent_duplicates`` dictates whether some measures should be taken
    against duplicate comments.
    
    ``allow_comments_field_name`` is a boolean field on the target model that,
    when evaluating to ``False``, prevents comments from being posted.

    ``send_notifications`` dictates whether notifications should be sent or
    not.

    """
    template_object_name = 'comment'

    preview_template_name = 'simple_comments/comment_preview.html'
    form_template_name = 'simple_comments/comment_form.html'
    list_template_name = 'simple_comments/comment_list.html'
    deleted_template_namae = 'simple_comments/comment_deleted.html'
    posted_template_name = 'simple_comments/comment_posted.html'
    
    use_akismet = False
    use_control_question = False
    use_honeypot = False
    
    user_comments = False
    user_can_delete = False
    
    autoclose_after = None
    autoclose_after_field_name = None
    
    prevent_duplicates = True
    
    allow_comments_field_name = None
    
    send_notifications = False

    # require_moderation = False
    # confirm_delete = True
    # comment_markup

    order_by = 'pub_date'
    paginate_by = 25

    def __init__(self, configuration_key, model):
        self.configuration_key = configuration_key
        self.model = model

    def get_exclude(self):
        """Return a list of fields to exclude when generating a form using
        ``get_form()``. Defaults to the basic fields of the ``BaseComment`` we
        want to exclude.
        
        Subclasses may override this method to alter the list of fields to
        exlcude, albeit it's probably easier to just set an ``exclude``
        attribute.
        
        """
        exclude = ['user', 'user_username', 'pub_date', 'ip_address', 'target']
        if self.user_comments:
            exclude = exclude + ['author_name', 'author_email',
                                 'author_website']
        return exclude
    exclude = property(fget=lambda self: self.get_exclude())
    
    def days_since_target_was_published(self, target):
        """Return the number of days that have passed since ``target`` was
        published.
        
        """
        now = datetime.datetime.now()
        published = getattr(target, self.autoclose_after_field_name)
        diff = datetime.date(now.year, now.month, now.day) - \
            datetime.date(published.year, published.month, published.day)
        return diff.days
    
    def allow_comments(self, target):
        """Return a boolean dictating whether comments are allowed for
        ``target`` or not.
        
        """
        if self.allow_comments_field_name is not None and \
           not getattr(target, self.allow_comments_field_name):
            return False

        if self.autoclose_after_field_name is not None and \
           self.autoclose_after is not None:
            days_since = self.days_since_target_was_published(target)
            return days_since < self.autoclose_after
        return True

    def get_target_owner(self, target):
        """Return the owner (``User`` instance) of target."""
        return None

    def get_duplicate(self, target, comment):
        """Try to determine if a duplicate of `comment` exists. If entries
        posted by the same author, with the same content, exist for the same
        day the latest "duplicate" record is returned. Otherwise return
        ``None``.

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
        return reverse('simple_comments_comment_posted',
                       args=[self.configuration_key, target.pk, comment.pk])
            
    def get_post_delete_redirect_url(self, target):
        """Return a URL to redirect to after a successful comment delete."""
        return reverse('simple_comments_comment_deleted',
                       args=[self.configuration_key, target.pk])

    def get_form(self):
        """Return a form-class to use when creating comments.
        
        Subclasses can override this method to return a custom form.        

        """
        return modelform_factory(self.model, fields=None, exclude=self.exclude)

    def get_spam_prevention_forms(self):
        """Return a list containing spam prevention forms."""
        forms = []
        if self.use_akismet:
            forms.append(comment_forms.AkismetForm)
        if self.use_control_question:
            forms.append(comment_forms.EarTriviaForm)
        if self.use_honeypot:
            forms.append(comment_forms.HoneypotForm)
        return forms
    
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

    def get_notification_users(self, target):
        """Return an iterable of ``User`` instances that should be notified
        when a comment is made on ``target``.
        
        """
        return [self.get_target_owner(target)]

    def send_notifications(self, comment):
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

    # Views

    def create_comment(self, request, target_id, extra_context=None):
        target = get_object_or_404(self.model.get_target_model(), pk=target_id)

        if not self.allow_comments(target) or \
           (self.user_comments and not request.user.is_authenticated()):
            return http.HttpResponseForbidden()

        extra_context = extra_context or {}

        is_preview = request.POST.get('submit', '').lower() == 'preview' or \
                     request.POST.get('preview', None) is not None
        extra_context.update({ 'is_preview': is_preview })

        data = request.POST or None
        form = self.get_form()(data=data)
        spam_prevention_forms = [f(request=request, data=data) for f in \
                                 self.get_spam_prevention_forms()]
        is_valid = form.is_valid() and \
                   all([f.is_valid() for f in spam_prevention_forms])

        extra_context = {
            'form': form,
            'spam_prevention_forms': spam_prevention_forms,
            'target': target,
            'configuration': self,
        }

        if not is_valid or request.method == 'GET':
            return direct_to_template(request,
                                      template=self.form_template_name,
                                      extra_context=extra_context)

        # Do note that we're not actually persisting the instance here, we're
        # calling save because we need an instance when we render the preview
        # template.
        comment = form.save(commit=False)

        if self.user_comments:
            comment.user = request.user
            comment.denormalize_user_instance()

        comment.target = target
        comment.ip_address = request.META.get("REMOTE_ADDR", None)
        extra_context = extra_context or {}
        extra_context.update({ self.template_object_name: comment })

        if is_preview:
            return direct_to_template(request,
                                      template=self.preview_template_name,
                                      extra_context=extra_context)

        # Try to prevent accidental duplicate postings by finding a *very*
        # similar comment and use that instead of saving a new one.
        duplicate = self.get_duplicate(target, comment)
        if duplicate is not None:
            comment = duplicate
        else:
            comment.save()

        self.send_notifications(comment)

        post_save_redirect_url = self.get_post_save_redirect_url(target,
                                                                 comment)
        return http.HttpResponseRedirect(post_save_redirect_url)

    def delete_comment(self, request, target_id, comment_id):
        target = get_object_or_404(self.model.get_target_model(), pk=target_id)
        comment = get_object_or_404(self.model, pk=comment_id)

        if not self.has_permission_to_delete(comment, request.user, request):
            return http.HttpResponseForbidden()

        comment.delete()

        post_delete_redirect_url = \
            config.get_post_delete_redirect_url(target)
        return http.HttpResponseRedirect(post_delete_redirect_url)

    def comment_list(self, request, target_id=None, extra_context=None):
        queryset = self.model._default_manager.all().select_related()
        queryset = queryset.order_by(self.order_by)

        if target_id is not None:
            queryset = queryset.filter(target=target_id)

        extra_context = extra_context or {}
        extra_context.update({
            'target_id': target_id,
            'configuration': self,
        })

        return object_list(request, queryset=queryset,
                           paginate_by=self.paginate_by,
                           template_object_name=self.template_object_name,
                           template_name=self.list_template_name,
                           extra_context=extra_context)

    def comment_posted(self, request, target_id, comment_id,
                       extra_context=None):
        target = get_object_or_404(self.model.get_target_model(), pk=target_id)
        comment = get_object_or_404(self.model, pk=comment_id)
        extra_context = extra_context or {}
        return direct_to_template(request,
                                  template=self.posted_template_name,
                                  extra_context=extra_context)

    def comment_deleted(self, request, target_id, extra_context=None):
        target = get_object_or_404(self.model.get_target_model(), pk=target_id)
        extra_context = extra_context or {}
        return direct_to_template(request,
                                  template=self.deleted_template_name,
                                  extra_context=extra_context)


class CommentConfigurationAlreadyRegistered(Exception):
    pass


class CommentConfigurationNotRegistered(Exception):
    pass


class CommentConfigurations(object):
    """Register comment models and configurations."""
    
    __shared_state = {
        'configurations': {},
    }
    
    def __init__(self):
        self.__dict__ = self.__shared_state
    
    def register(self, configuration_key, comment_model,
                 configuration_class=CommentConfiguration):
        """Register ``comment_model`` and ``configuration_class`` against
        ``configuration_key``. If configuration class is not given the default
        ``CommentConfiguration`` will be used.
        
        """
        try:
            self.configurations[configuration_key]
            raise CommentConfigurationAlreadyRegistered
        except KeyError:
            configuration = configuration_class(configuration_key,
                                                comment_model)
            self.configurations[configuration_key] = configuration
    
    def unregister(self, configuration_key):
        """Unregister model and configuration matching ``configuration_key``."""
        try:
            del(self.configurations[configuration_key])
        except KeyError:
            raise CommentConfigurationNotRegistered
    
    def get_configuration(self, configuration_key):
        """Return the comment model and configuration associated with
        ``configuration_key``.
        
        """
        try:
            return self.configurations[configuration_key]
        except KeyError:
            raise CommentConfigurationNotRegistered

    def all_configurations(self):
        return self.configurations.items()


configurations = CommentConfigurations()

all_configurations= configurations.all_configurations
register = configurations.register
unregister = configurations.unregister
get_configuration = configurations.get_configuration
