from rest_framework import serializers
from datetime import datetime
from django.utils import timezone


class DateSerializer(serializers.Serializer):
    date = serializers.CharField(required=False)

    def validate_date(self, data):
        if data:
            try:
                date = datetime.strptime(data, '%Y-%m-%d').date()

                if date >= timezone.now().date():
                    raise serializers.ValidationError(["Date should be less than current date"])
            except ValueError:
                raise serializers.ValidationError(["Invalid Date Format. Please use YYYY-MM-DD"])
            return date
        return data



