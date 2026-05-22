from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from .models import CustomUser
from events.models import TicketingConfig, Event

from services.ticketing.script_1_gen import generate_ticket
from services.ticketing.script_2_mail import send_ticket_email
from services.ticketing.mongo_helper import MongoDBClient
from services.ticketing.gsheets_helper import GSheetsHelper

@admin.action(description='✅ Generate and Email Tickets for selected users')
def generate_and_email_tickets(modeladmin, request, queryset):
    config = TicketingConfig.objects.first()
    event = Event.objects.first()
    form = getattr(event, 'form', None) if event else None
    
    if not config:
        modeladmin.message_user(request, "Ticketing Configuration is missing.", messages.ERROR)
        return
        
    try:
        mongo_client = MongoDBClient(config)
        gsheets_client = GSheetsHelper(
            config, 
            custom_sheet_link=form.google_sheet_link if form else None, 
            custom_sheet_name=form.sheet_name if form else None
        )
    except Exception as e:
        modeladmin.message_user(request, f"Database Connection Error: {e}", messages.ERROR)
        return

    success_count = 0
    for user in queryset:
        if user.email:
            full_name = f"{user.first_name} {user.last_name}".strip()
            
            # 1. Generate & Email
            ticket_path = generate_ticket(user.email, user.first_name, user.last_name, config)
            email_success = send_ticket_email(user.email, ticket_path, config)
            
            # 2. Save ticket to Django User Model AND Update Status
            if ticket_path:
                user.ticket_file.name = ticket_path
                user.registration_status = 'approved' 
                user.save()
            
            # 3. Update MongoDB
            attendee = mongo_client.find_attendee_by_email_and_name(user.email, full_name)
            if attendee:
                # Fixed Key: Uses "Attendee ID" to match MongoDB exactly
                att_id = attendee.get('Attendee ID')
                if att_id:
                    mongo_client.update_attendee_field(att_id, config.col_ticket_status, "Generated")
                    if email_success:
                        mongo_client.update_attendee_field(att_id, config.col_email_status, "Sent")
                        mongo_client.update_attendee_field(att_id, config.col_ticket_status, "Sent")
            
            # 4. Update Google Sheets
            if email_success:
                gsheets_client.update_attendee_status(user.email, "Sent", "Sent")
            else:
                gsheets_client.update_attendee_status(user.email, "Generated", "Failed")

            success_count += 1
            
    modeladmin.message_user(
        request, 
        f'Successfully generated, emailed, and synced tickets for {success_count} users.', 
        messages.SUCCESS
    )

@admin.action(description='❌ Reject selected users (Marks as Full/Rejected)')
def reject_selected_users(modeladmin, request, queryset):
    config = TicketingConfig.objects.first()
    event = Event.objects.first()
    form = getattr(event, 'form', None) if event else None
    
    try:
        gsheets_client = GSheetsHelper(
            config, 
            custom_sheet_link=form.google_sheet_link if form else None, 
            custom_sheet_name=form.sheet_name if form else None
        ) if config else None
    except:
        gsheets_client = None

    count = 0
    for user in queryset:
        user.registration_status = 'rejected'
        user.save()
        
        if gsheets_client:
            gsheets_client.update_attendee_status(user.email, "Rejected", "N/A")
        
        count += 1
        
    modeladmin.message_user(request, f'Successfully rejected {count} users.', messages.WARNING)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_registered', 'registration_status')
    search_fields = ('email', 'first_name', 'last_name')
    actions = [generate_and_email_tickets, reject_selected_users] 
    fieldsets = UserAdmin.fieldsets + (
        ('Event Details', {'fields': ('resume', 'ticket_file', 'is_registered', 'registration_status')}),
    )