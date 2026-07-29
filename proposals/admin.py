from django.contrib import admin
from .models import Proposal


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'rfp', 'status', 'estimated_cost', 'estimated_timeline_weeks', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'executive_summary')
    filter_horizontal = ('referenced_projects',)