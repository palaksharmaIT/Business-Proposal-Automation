from django.contrib import admin
from .models import HistoricalProject


@admin.register(HistoricalProject)
class HistoricalProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project_type', 'actual_cost', 'actual_duration_weeks', 'is_indexed')
    list_filter = ('project_type', 'is_indexed')
    search_fields = ('title', 'client_name', 'description', 'tech_stack')