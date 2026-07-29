from django.contrib import admin
from .models import RFP


@admin.register(RFP)
class RFPAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'uploaded_at')
    list_filter = ('status',)
    search_fields = ('title', 'extracted_text')