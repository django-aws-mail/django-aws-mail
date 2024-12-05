from django import forms

from django_json_widget.widgets import JSONEditorWidget

from django_aws_mail.models import Delay, Bounce, Complaint


class DelayForm(forms.ModelForm):

    class Meta:
        model = Delay
        fields = '__all__'
        widgets = {
            'delay': JSONEditorWidget(width='80%'),
            'mail': JSONEditorWidget(width='80%'),
        }


class BounceForm(forms.ModelForm):

    class Meta:
        model = Bounce
        fields = '__all__'
        widgets = {
            'bounce': JSONEditorWidget(width='80%'),
            'mail': JSONEditorWidget(width='80%'),
        }


class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = '__all__'
        widgets = {
            'complaint': JSONEditorWidget(width='80%'),
            'mail': JSONEditorWidget(width='80%'),
        }
