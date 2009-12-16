from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.db.models import signals

from simple_comments.options import NOTIFICATION_LABEL
from simple_comments import options

# Create tables for the notification-app if available.

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type(NOTIFICATION_LABEL, _("Comment"), _("someone has commented"))

    signals.post_syncdb.connect(create_notice_types, sender=notification)

else:
    print "Skipping creation of NoticeTypes as notification app not found"
