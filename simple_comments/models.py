import datetime

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

BODY_MAX_LENGTH = getattr(settings, 'SIMPLE_COMMENTS_BODY_MAX_LENGTH', 3000)

class BaseComment(models.Model):
    """Abstract base class used to create comment models.
    
    All subclasses **must** implement a ``models.ForeignKey`` specifying the
    model of the instance comments should refence. This field **must** have the
    name ``target``.
    
    The class works well with authenticated users as well as manual input of
    ``author_name`` and ``author_email``. If a ``User`` instance is supplied
    these fields will be retrieved from that instance. Data retrieved from a
    supplied user will always take precedence.
    
    """
    user = models.ForeignKey(User, null=True, blank=True)
    # Store the username here as a simple act of denormalization. Using
    # convenience methods (such as get_absolute_url) on nullable foreign keys
    # can be expensive. We're betting on that the id or username will be
    # sufficient to reconstruct URLs in most cases.
    user_username = models.CharField(max_length=30, blank=True)
    
    author_name = models.CharField(max_length=61)
    author_email = models.EmailField()
    author_website = models.URLField(blank=True)
    
    body = models.TextField(max_length=BODY_MAX_LENGTH)
    
    pub_date = models.DateTimeField(default=datetime.datetime.now)
    
    ip_address  = models.IPAddressField(blank=True, null=True)
    
    def __init__(self, *args, **kwargs):
        """Override to make sure that a ``ForeignKeyField`` named ``target``
        exists on subclasses.
        
        """
        super(BaseComment, self).__init__(*args, **kwargs)
        try:
            target_field = self._meta.get_field('target')
            if not issubclass(target_field.__class__, models.ForeignKey):
                raise TypeError
        except (models.FieldDoesNotExist, TypeError):
            raise TypeError(u'Subclasses of BaseComment must add a foreign key field named target')
    
    def denormalize_user_instance(self):
        """Set the author name, email and username on the model if a ``User``
        instance has been supplied.
        
        """
        user = self.user
        if user is not None:
            if user.first_name or user.last_name:
                self.author_name = user.get_full_name()
            else:
                # Fall back on the user's username if neither first- nor last
                # names were set on the user instance.
                self.author_name = user.username
            self.author_email = user.email
            self.user_username = user.username

    def get_absolute_url(self):
        return '%s#comment-%s' % (self.target.get_absolute_url(), self.pk)

    def save(self, *args, **kwargs):
        self.denormalize_user_instance()
        super(BaseComment, self).save(*args, **kwargs)
    
    @classmethod
    def get_target_model(cls):
        """Return the model that we're referencing in the required
        ``ForeignKey`` field of subclasses.
    
        """
        return cls._meta.get_field('target').rel.to

    class Meta:
        abstract = True
        get_latest_by = 'pub_date'
