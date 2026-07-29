from django.contrib import admin
from .models import ProposalDelivery


@admin.register(ProposalDelivery)
class ProposalDeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'proposal', 'sent_to_email', 'delivery_status', 'approval_status', 'sent_at')
    list_filter = ('delivery_status', 'approval_status')
    search_fields = ('sent_to_email',)