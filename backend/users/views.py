import uuid
import json
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser
from events.models import Event, TicketingConfig

from services.ticketing.mongo_helper import MongoDBClient
from services.ticketing.gsheets_helper import GSheetsHelper
from services.ticketing.cloudinary_helper import CloudinaryHelper

@api_view(['POST'])
@permission_classes([AllowAny])
def auth_action(request):
    """Handles both Login and Registration"""
    action = request.data.get('action')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({'error': 'Email and password are required.'}, status=400)

    if not email.endswith('@ietdavv.edu.in'):
        return Response({'error': 'Please use your valid @ietdavv.edu.in college ID.'}, status=400)

    if action == 'register':
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if CustomUser.objects.filter(email=email).exists():
            return Response({'error': 'This College ID is already registered.'}, status=400)
            
        user = CustomUser.objects.create_user(
            username=email, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'message': 'Registration successful!'})
        
    elif action == 'login':
        user = authenticate(username=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'message': 'Login successful!'})
        else:
            return Response({'error': 'Invalid College ID or Password.'}, status=401)
            
    return Response({'error': 'Invalid action.'}, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated]) 
def dashboard_view(request):
    user = request.user
    event = Event.objects.filter(is_completed=False).first()
    config = TicketingConfig.objects.first()

    if request.method == 'POST':
        dynamic_answers = json.loads(request.POST.get('answers', '{}'))
        form = getattr(event, 'form', None)
        
        # --- Process Dynamic File Uploads to Cloudinary ---
        if request.FILES and config:
            try:
                cloudinary_client = CloudinaryHelper(config)
                for key, file_obj in request.FILES.items():
                    if key.startswith('file_'):
                        label = key.replace('file_', '', 1)
                        
                        # Fix: Get the original filename without extension to use as public_id
                        # This stops Cloudinary from generating random strings
                        original_name, _ = os.path.splitext(file_obj.name)
                        safe_public_id = f"{user.first_name}_{original_name}".replace(" ", "_")
                        
                        folder_path = f"event_files/{user.email.split('@')[0]}"
                        
                        link = cloudinary_client.upload_file(
                            file_obj, 
                            folder_name=folder_path,
                            public_id=safe_public_id
                        )
                        
                        if link:
                            dynamic_answers[label] = link
            except Exception as e:
                print(f"Cloudinary Upload Error: {e}")
        
        user.registration_data = dynamic_answers
        user.is_registered = True
        
        # --- AUTO TICKET GENERATION LOGIC ---
        ticket_status = "Pending"
        email_status = "Pending"
        
        auto_generate = getattr(config, 'auto_generate_tickets', False)
        
        if auto_generate:
            try:
                from services.ticketing.script_1_gen import generate_ticket
                from services.ticketing.script_2_mail import send_ticket_email
                
                ticket_path = generate_ticket(user.email, user.first_name, user.last_name, config)
                email_success = send_ticket_email(user.email, ticket_path, config)
                
                if ticket_path:
                    user.ticket_file.name = ticket_path
                    user.registration_status = 'approved'
                    ticket_status = "Generated" if not email_success else "Sent"
                    email_status = "Failed" if not email_success else "Sent"
            except Exception as e:
                print(f"Auto-Ticket Generation Error: {e}")
        else:
            # If auto-generation is off, send the standard "Under Review" confirmation email
            try:
                from services.ticketing.script_2_mail import send_confirmation_email
                send_confirmation_email(user.email, user.first_name, config)
            except Exception as e:
                print(f"Confirmation Mail Error: {e}")

        user.save()
        
        # --- Sync to MongoDB and Google Sheets ---
        try:
            if config:
                mongo_client = MongoDBClient(config)
                gsheets_client = GSheetsHelper(config, custom_sheet_link=form.google_sheet_link if form else None, custom_sheet_name=form.sheet_name if form else None)
                
                attendee_id = str(uuid.uuid4())
                full_name = f"{user.first_name} {user.last_name}".strip()
                
                attendee_data = {
                    config.col_name: full_name,
                    config.col_email: user.email,
                    "Attendee ID": attendee_id,
                    config.col_ticket_status: ticket_status, # Passes accurate status!
                    config.col_email_status: email_status,   # Passes accurate status!
                    **dynamic_answers 
                }
                
                mongo_client.insert_full_attendee(attendee_data)
                gsheets_client.append_attendee(attendee_data)
        except Exception as e:
            print(f"Sync Warning: {e}")
        
        return Response({'message': 'Registration completed successfully!'})

    # --- Handle GET request ---
    ticket_url = request.build_absolute_uri(user.ticket_file.url) if user.ticket_file else None
    
    form_fields = []
    if event and hasattr(event, 'form'):
        form_fields = event.form.fields.all().values('id', 'label', 'field_type', 'options', 'is_required')

    return Response({
        'user': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_registered': user.is_registered,
            # Passes the new status to Next.js so it can show "Under Review" or "Rejected"
            'registration_status': getattr(user, 'registration_status', 'pending'), 
            'ticket_url': ticket_url,
        },
        'event': {
            'form_fields': list(form_fields),
            'custom_theme_code': getattr(event, 'custom_theme_code', '') if event else ''
        }
    })