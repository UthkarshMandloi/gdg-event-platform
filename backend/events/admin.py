from django.contrib import admin
from django.contrib import messages
from .models import Event, Speaker, TicketingConfig, RegistrationForm, FormField
from services.ticketing.gsheets_helper import GSheetsHelper

# Changed to StackedInline to look exactly like Google Form blocks!
# Extra=0 ensures no blank blocks appear automatically, and gives a clean "Delete" option.
class FormFieldInline(admin.StackedInline):
    model = FormField
    extra = 0 

@admin.register(RegistrationForm)
class RegistrationFormAdmin(admin.ModelAdmin):
    list_display = ('event', 'google_sheet_link')
    inlines = [FormFieldInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        config = TicketingConfig.objects.first()
        if not config:
            messages.warning(request, "Form saved, but Google Sheet headers were NOT synced because TicketingConfig is missing.")
            return
            
        try:
            gsheets = GSheetsHelper(config, custom_sheet_link=form.instance.google_sheet_link, custom_sheet_name=form.instance.sheet_name)
            custom_labels = list(form.instance.fields.values_list('label', flat=True))
            was_updated, headers = gsheets.sync_sheet_headers(custom_labels)
            
            if was_updated:
                messages.success(request, f"Successfully created/updated header row in Google Sheets: {headers}")
            else:
                messages.info(request, "Google Sheet headers checked. No changes were needed.")
                
        except Exception as e:
            messages.error(request, f"Error syncing with Google Sheets: {e}")

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date')

@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_revealed')
    list_editable = ('is_revealed',) 

@admin.register(TicketingConfig)
class TicketingConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if TicketingConfig.objects.exists():
            return False
        return super().has_add_permission(request)