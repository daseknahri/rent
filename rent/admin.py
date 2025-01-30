from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path
from django.urls import reverse

from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

from .views import admin_dashboard
from .models import BusinessExpenditure, Car, Client, Reservation, CarExpenditure, Payment, Driver
from django.utils.html import format_html
from django import forms
from django.contrib import admin
from django.db import transaction
from django.template.response import TemplateResponse
from django.utils.translation import gettext


@staff_member_required
def revenue_report(request):
    """
    Custom view for displaying revenue and expenditure report.
    """
    # Group reservations by month and calculate revenue
    data = (
        Reservation.objects.annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(
            total_revenue=Sum('total_cost'),
            total_expenditures=Sum('car__expenditures__cost'),
        )
        .order_by('month')
    )
    return render(request, 'admin/revenue_report.html', {'data': data})
class ClientAdminForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    # Override the default widget for image fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['identity_card_image'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['driver_license_image'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['passport_image'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})

@admin.action(description="Delete selected objects")
def custom_delete_selected(modeladmin, request, queryset):
    with transaction.atomic():  # Ensure database integrity
        for obj in queryset:
            obj.delete()  # Call the model's delete() method

class CustomAdminSite(admin.AdminSite):
    
    site_header = "TWINS T.B CAR"
    site_title = "Car Rental Management"
    index_title = "Welcome to Rent Administration"
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('revenue-report/', self.admin_view(revenue_report), name='revenue_report'),
            path('dashboard/', admin_dashboard, name='dashboard')
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        context = super().each_context(request)
        context.update(admin_dashboard(request))
        if request.path == reverse('admin:index'):  # Check if it's the dashboard
            extra_context = extra_context or {}
            extra_context['custom_links'] = [
                {'url': reverse('revenue_report'), 'name': 'Revenue Report'},
            ]
            
        return super().index(request, context)
    def app_index(self, request, app_label, extra_context=None):
        """Display the app index page, listing all models."""
        app_list = self.get_app_list(request, app_label)
        context = {
            **self.each_context(request),
            "title": gettext("%(app)s administration") % {"app": app_label},
            "app_list": app_list,
            "app_label": app_label,
            **(extra_context or {}),
        }
        return TemplateResponse(request, self.app_index_template or "admin/app_index.html", context)
    
    def each_context(self, request):
        context = super().each_context(request)
        # Add app_list to the context for all pages
        context['app_list'] = self.get_app_list(request)
        return context

admin_site = CustomAdminSite(name='custom_admin')

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    search_fields = ['name']

### INLINE FOR EXPENDITURES IN CARS ###
class CarExpenditureInline(admin.TabularInline):
    model = CarExpenditure
    extra = 1  # Allows admin to add expenditures directly in the car interface
    readonly_fields = ('date',)  # Prevent editing the date
    classes = ('collapse',)

class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0  # Prevent adding new reservations from the car page
    readonly_fields = ('total_cost', 'payment_status', 'total_paid')
    fields = ('total_cost', 'total_paid', 'start_date', 'end_date')  # Include all fields
    classes = ('collapse',)  # Optional: Add collapsible behavior
'''
class ReservationInline(admin.TabularInline):
    model = Reservation
    extra = 0
    fields = ('start_date', 'end_date', 'total_paid')
    readonly_fields = ('start_date', 'end_date', 'total_paid')
    template = 'admin/edit_inline/tabular_custom.html'

'''
### CAR ADMIN ###
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'plate_number', 'daily_rate', 'total_expenditure','is_available')
    list_filter = ('daily_rate',)  # Filter by car brand and year
    search_fields = ('plate_number', 'name')  # Search by plate number, brand, or model
    readonly_fields = ('total_expenditure',)  # Prevent editing total expenditure
 #   inlines = [CarExpenditureInline, ReservationInline]  # Add expenditures inline
    actions = [custom_delete_selected]

    fieldsets = (
        ('Car Information', {
            'fields': ('name', 'plate_number', 'year', 'image', 'daily_rate')
        }),
        ('Expenditure', {
            'fields': ('total_expenditure',)
        }),
    )
    def get_actions(self, request):
        # Call the parent method to get all actions
        actions = super().get_actions(request)
        # Remove the default delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

### CLIENT ADMIN ###
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm
    list_display = ('name', 'phone_number', 'rating', 'total_amount_paid', 'total_amount_due', 'show_identity_card')
    list_editable = ('rating',) 
    search_fields = ('name', 'phone_number')  # Search by username, email, or phone
    readonly_fields = ('total_amount_paid', 'total_amount_due')  # Prevent editing payment info
    list_filter = ('rating',)
    actions = [custom_delete_selected]
    fieldsets = (
        ('Client Information', {
            'fields': ('name', 'phone_number', 'address')
        }),
        ('documents', {
            'fields': ('identity_card_image', 'driver_license_image', 'passport_image')
        }),
        ('Payment Details', {
            'fields': ('total_amount_paid', 'total_amount_due')
        }),
    )
    def show_identity_card(self, obj):
        if obj.identity_card_image:
            return format_html('<img src="{}" width="50" height="50" />', obj.identity_card_image.url)
        return "No Image"
    show_identity_card.short_description = "Identity Card"

    def get_actions(self, request):
        # Call the parent method to get all actions
        actions = super().get_actions(request)
        # Remove the default delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


### INLINE FOR PAYMENTS IN RESERVATIONS ###
class PaymentInline(admin.StackedInline):
    model = Payment
    fields = ('amount',)
    extra = 1  # Allows admin to add payments directly in the reservation interface



### RESERVATION ADMIN ###
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'car', 'client', 'start_date', 'end_date', 'total_cost', 'total_paid', 'pdf_link')
    autocomplete_fields = ['drivers']
    list_filter = ('payment_status', 'start_date', 'end_date')  # Filter by payment status and rental period
    search_fields = ('car__plate_number', 'client__name')  # Search by car or client
    readonly_fields = ('total_cost', 'payment_status', 'total_paid', 'pdf_link')  # Prevent editing calculated fields
    inlines = [PaymentInline]  # Add payments inline
    actions = [custom_delete_selected]
    fieldsets = (
        ('Reservation Details', {
            'fields': ('car', 'client', 'drivers', 'start_date', 'end_date')
        }),
        ('Payment Information', {
            'fields': ('total_paid', 'total_cost', 'payment_status')
        }),
    )
    def pdf_link(self, obj):
        """
        Show a link to download the PDF in the admin interface.
        """
        if obj.pdf_receipt:
            return format_html('<a href="/media/{}" target="_blank">Download Receipt</a>', obj.pdf_receipt)
        return "No PDF Available"

    pdf_link.short_description = "PDF Receipt"
    def save_model(self, request, obj, form, change):
        """
        Override save to generate the PDF when the reservation is created or updated.
        """
        super().save_model(request, obj, form, change)
        obj.generate_pdf_receipt()
    def get_actions(self, request):
        # Call the parent method to get all actions
        actions = super().get_actions(request)
        # Remove the default delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


### PAYMENT ADMIN ###
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'amount', 'payment_date')
    list_filter = ('payment_date',)  # Filter by payment date
    search_fields = ('reservation__car__plate_number', 'reservation__client__name')  # Search by car or client
    readonly_fields = ('payment_date',)  # Prevent editing payment date
    actions = [custom_delete_selected]

    fieldsets = (
        ('Payment Details', {
            'fields': ('reservation', 'amount', 'payment_date')
        }),
    )
    def get_actions(self, request):
        # Call the parent method to get all actions
        actions = super().get_actions(request)
        # Remove the default delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


### CAR EXPENDITURE ADMIN ###
@admin.register(CarExpenditure)
class CarExpenditureAdmin(admin.ModelAdmin):
    list_display = ('car', 'description', 'cost', 'date')
    list_filter = ('date', 'car')  # Filter by expenditure date
    search_fields = ('car__name', 'description')  # Search by car plate number or description
    readonly_fields = ('date',)  # Prevent editing the date
    actions = [custom_delete_selected]

    fieldsets = (
        ('Expenditure Information', {
            'fields': ('car', 'description', 'cost', 'date')
        }),
    )
    def get_actions(self, request):
        # Call the parent method to get all actions
        actions = super().get_actions(request)
        # Remove the default delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(BusinessExpenditure)
class BusinessExpenditureAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date')
    list_filter = ('date',)
    search_fields = ('description',)

admin_site.register(User, UserAdmin)
#admin_site.register(Group)
admin_site.register(Car, CarAdmin)
admin_site.register(Client, ClientAdmin)
admin_site.register(Reservation, ReservationAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(CarExpenditure, CarExpenditureAdmin)
admin_site.register(Driver, DriverAdmin)
admin_site.register(BusinessExpenditure, BusinessExpenditureAdmin)
