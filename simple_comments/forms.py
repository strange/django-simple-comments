from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.encoding import smart_str

class SpamPreventionForm(forms.Form):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SpamPreventionForm, self).__init__(*args, **kwargs)


class EarTriviaForm(SpamPreventionForm):
    """Form with the single purpose of making it difficult for a machine to
    pass validation by adding a question that is trivial to answer most
    humans.

    """
    (ONE, TWO) = (0, 1)
    CHOICES = ((ONE, 'One'), (TWO, 'Two'))
    CORRECT_ANSWER = TWO

    question = forms.ChoiceField(choices=CHOICES,
                                 label=u"How many ears does an average human "
                                       u"have?")

    def __init__(self, *args, **kwargs):
        super(EarTriviaForm, self).__init__(*args, **kwargs)

    def clean_question(self):
        value = self.cleaned_data["question"]
        if int(value) != self.CORRECT_ANSWER:
            raise forms.ValidationError(u'Think again!')
        return value


class HoneypotForm(SpamPreventionForm):
    """Form that adds a honeypot field -- a field that aims to lure
    spammers into entering data that would invalidate the form.

    """
    honeypot = forms.CharField(required=False)

    def clean_honeypot(self):
        """Check that nothing's been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]
        if value:
            raise forms.ValidationError(u'This field must remain empty.')
        return value


class AkismetForm(SpamPreventionForm):
    """Form that adds the ability to check submitted data via the Wordpress
    Akismet spam filter.

    """
    def clean(self):
        """Run the body of the comment against the akismet API."""
        from akismet import Akismet
        data = {
            'comment_type': 'comment',
            'referrer': self.request.META.get('HTTP_REFERER', ''),
            'user_ip': self.request.META.get('REMOTE_ADDR', ''),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', '')
        }
        body = self.cleaned_data.get('body')
        blog_url = 'http://%s/' % Site.objects.get_current().domain

        api = Akismet(key=settings.AKISMET_API_KEY, blog_url=blog_url)

        if api.verify_key():
            if api.comment_check(smart_str(body), data=data):
                raise forms.ValidationError(u"Your comment appears to be "
                                            u"spam.")
        return self.cleaned_data
