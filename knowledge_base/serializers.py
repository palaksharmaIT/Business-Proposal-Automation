from rest_framework import serializers
from .models import HistoricalProject


class HistoricalProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalProject
        fields = '__all__'