from django.contrib import admin

from django_aws_mail.models import Delay, Bounce, Complaint
from django_aws_mail.forms import DelayForm, BounceForm, ComplaintForm
from django_aws_mail.utils import admin_link


@admin.register(Delay)
class DelayAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated', 'delay_type', 'count', 'destination', 'user_link')
    readonly_fields = ('created',)
    search_fields = ('destination',)
    ordering = ('-updated',)
    form = DelayForm

    list_select_related = ('user',)

    @admin.display(ordering='user__email')
    @admin_link('user', 'User')
    def user_link(self, user):
        return user


@admin.register(Bounce)
class BounceAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated', 'bounce_type', 'bounce_sub_type', 'bounce_status',
                    'count', 'destination', 'user_link')
    readonly_fields = ('created',)
    search_fields = ('destination',)
    ordering = ('-updated',)
    form = BounceForm

    list_select_related = ('user',)

    @admin.display(ordering='bounce__bouncedRecipients__0__status')
    def bounce_status(self, obj):
        try:
            return obj.bounce['bouncedRecipients'][0]['status']
        except KeyError:
            return None

    @admin.display(ordering='user__email')
    @admin_link('user', 'User')
    def user_link(self, user):
        return user


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('created', 'updated', 'complaint_type', 'complaint_subtype', 'count',
                    'destination', 'user_link')
    readonly_fields = ('created',)
    search_fields = ('destination',)
    ordering = ('-updated',)
    form = ComplaintForm

    list_select_related = ('user',)

    @admin.display(ordering='complaint__complaintSubType')
    def complaint_subtype(self, obj):
        try:
            return obj.complaint['complaintSubType']
        except KeyError:
            return None

    @admin.display(ordering='user__email')
    @admin_link('user', 'User')
    def user_link(self, user):
        return user
