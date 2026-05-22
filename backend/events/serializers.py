from rest_framework import serializers
from .models import Event, Speaker

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'date', 'venue', 'is_completed', 'custom_theme_code', 'custom_theme_file']

class SpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Speaker
        fields = ['name', 'bio', 'is_revealed']