from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event, Speaker
from .serializers import EventSerializer, SpeakerSerializer

@api_view(['GET'])
def get_event_details(request):
    # Get the active event (first one that isn't completed)
    active_event = Event.objects.filter(is_completed=False).first()
    
    # Get all past events
    past_events = Event.objects.filter(is_completed=True).order_by('-date')
    
    # ONLY get speakers where you have flipped the 'is_revealed' switch to True in Admin!
    speakers = Speaker.objects.filter(is_revealed=True)
    
    active_event_data = EventSerializer(active_event).data if active_event else None
    past_events_data = EventSerializer(past_events, many=True).data
    speaker_data = SpeakerSerializer(speakers, many=True).data
    
    return Response({
        'event': active_event_data,
        'past_events': past_events_data,
        'speakers': speaker_data
    })