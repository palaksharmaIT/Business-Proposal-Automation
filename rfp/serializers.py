from rest_framework import serializers
from .models import RFP


class RFPSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFP
        fields = ['id', 'title', 'file', 'extracted_text', 'extracted_requirements', 'status', 'uploaded_at']
        read_only_fields = ['extracted_text', 'extracted_requirements', 'status', 'uploaded_at']