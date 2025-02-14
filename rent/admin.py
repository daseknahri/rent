from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path
from django.urls import reverse

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _, gettext, get_language
from .views import admin_dashboard
from .models import BusinessExpenditure, Car, Client, Reservation, CarExpenditure, Payment, Driver, ExpenditureType
from django.utils.html import format_html
from django import forms
from django.contrib import admin
from django.db import transaction
from django.template.response import TemplateResponse
from django.http import JsonResponse



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
class DriverAdminForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = '__all__'

    # Override the default widget for image fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date_of_birth'].widget = forms.DateInput(attrs={'type': 'date'})

        self.fields['identity_card_front'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['identity_card_back'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['driver_license_front'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['driver_license_back'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['passport_image'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
class ClientAdminForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    # Override the default widget for image fields
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date_of_birth'].widget = forms.DateInput(attrs={'type': 'date'})

        self.fields['identity_card_front'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['identity_card_back'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['driver_license_front'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['driver_license_back'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        self.fields['passport_image'].widget.attrs.update({'capture': 'camera', 'accept': 'image/*'})
        if not self.instance.pk:
                self.fields['total_amount_paid'].widget = forms.HiddenInput()
                self.fields['total_amount_due'].widget = forms.HiddenInput()
        else:
                self.fields['total_amount_paid'].widget.attrs['readonly'] = True
                self.fields['total_amount_due'].widget.attrs['readonly'] = True

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = "__all__"
        widgets = {
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),  # Use HTML5 time input
            'dropoff_time': forms.TimeInput(attrs={'type': 'time'}),  # Use HTML5 time input
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
                self.fields['pickup_time'].widget = forms.HiddenInput()
                self.fields['dropoff_time'].widget = forms.HiddenInput()
                self.fields['total_paid'].widget = forms.HiddenInput()
                self.fields['payment_status'].widget = forms.HiddenInput()
                self.fields['total_cost'].widget.attrs['readonly'] = True

        else:
            # If it's an existing object (editing), you can modify the form
            self.fields['total_paid'].widget.attrs['readonly'] = True
            self.fields['payment_status'].widget.attrs['readonly'] = True


@admin.action(description=_("Delete selected objects"))
def custom_delete_selected(modeladmin, request, queryset):
    with transaction.atomic():  # Ensure database integrity
        for obj in queryset:
            obj.delete()  # Call the model's delete() method

class CustomAdminSite(admin.AdminSite):
    
    site_header = _("TWINS T.B CAR")
    site_title = _("Car Rental Management")
    index_title = _("Welcome to Administration")
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
                {'url': reverse('revenue_report'), 'name': _("Revenue Report")},
            ]
            
        return super().index(request, context)
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        # 🔥 Define custom model order
        custom_order = [
            "Reservation",
            "Car",
            "Client",
            "Payment",
            "CarExpenditure",
            "BusinessExpenditure",
        ]
        hidden_models = {"ExpenditureType", "Driver"}
        for app in app_list:
            app["models"] = [model for model in app["models"] if model["object_name"] not in hidden_models]

        for app in app_list:
            app["models"].sort(
                key=lambda model: custom_order.index(model["object_name"])
                if model["object_name"] in custom_order
                else len(custom_order)
            )

        return app_list
    def app_index(self, request, app_label, extra_context=None):
        """Display the app index page, listing all models."""
        app_list = self.get_app_list(request, app_label)
        context = {
            **self.each_context(request),
            "title": _("Dashboard"),
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
   # class Media:
    #    js = ('https://code.jquery.com/jquery-3.6.0.min.js', 'admin/js/custom_admin.js',)
    form = DriverAdminForm
    list_display = ('name', 'phone_number', 'show_identity_card')
    search_fields = ('name', 'identity_card_number') 
    actions = [custom_delete_selected]
    fieldsets = (
        (_('Driver Information'), {
            'fields': ('name', 'phone_number', 'address', 'date_of_birth', 'identity_card_number', 'driver_license_number')
        }),
        (_('documents'), {
            'fields': ('identity_card_front', 'identity_card_back', 'driver_license_front', 'driver_license_back', 'passport_image')
        }),
    )
    def show_identity_card(self, obj):
        if obj.identity_card_front:
            return format_html('<img src="{}" width="50" height="50" />', obj.identity_card_front.url)
        return _("No Image")
    show_identity_card.short_description = _("Identity Card")

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
    list_display = ('brand', 'model', 'plate_number', 'daily_rate', 'total_expenditure','is_available')
    list_filter = ('daily_rate', 'is_available',)  # Filter by car brand and year
    search_fields = ('plate_number', 'brand',)  # Search by plate number, brand, or model
    readonly_fields = ('total_expenditure',)  # Prevent editing total expenditure
 #   inlines = [CarExpenditureInline, ReservationInline]  # Add expenditures inline
    actions = [custom_delete_selected]

    fieldsets = (
        (_('Car Information'), {
            'fields': ('brand', 'model', 'plate_number', 'year', 'image', 'daily_rate')
        }),
        (_('Expenditure'), {
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
    class Media:
        js = ('https://code.jquery.com/jquery-3.6.0.min.js', 'admin/js/custom_admin.js',)
    form = ClientAdminForm
    list_display = ('name', 'phone_number', 'rating', 'total_amount_paid', 'total_amount_due', 'age','show_identity_card')
    list_editable = ('rating',) 
    search_fields = ('name', 'identity_card_number')  # Search by username, email, or phone
    list_filter = ('rating',)
    actions = [custom_delete_selected]
    fieldsets = (
        (_('Client Information'), {
            'fields': ('name', 'phone_number', 'address', 'date_of_birth', 'identity_card_number', 'driver_license_number')
        }),
        (_('documents'), {
            'fields': ('identity_card_front', 'identity_card_back', 'driver_license_front', 'driver_license_back', 'passport_image')
        }),
        (_('Payment Details'), {
            'fields': ('total_amount_paid', 'total_amount_due')
        }),
    )
    def show_identity_card(self, obj):
        if obj.identity_card_front:
            return format_html('<img src="{}" width="50" height="50" />', obj.identity_card_front.url)
        return _("No Image")
    show_identity_card.short_description = _("Identity Card")

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
    fields = ("amount",)
    extra = 1  # Allows admin to add payments directly in the reservation interface



### RESERVATION ADMIN ###
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    form = ReservationForm
    list_display = ('pk', 'car', 'client', 'start_date', 'end_date', 'total_cost', 'total_paid', 'status', 'pdf_link')
    autocomplete_fields = ['drivers']
    list_filter = ('payment_status', 'start_date', 'end_date')  
    search_fields = ('car__plate_number', 'client__name')  
    #readonly_fields = ('total_cost', 'payment_status', 'total_paid', 'pdf_link')  
    inlines = [PaymentInline]  
    actions = [custom_delete_selected, "mark_as_picked_up", "mark_as_returned"]
    change_form_template = "admin/rent/reservation/change_form.html"

    fieldsets = (
        (_("Reservation Details"), {  # Translated Section Title
            'fields': ('car', 'client', 'drivers', 'actual_daily_rate', 'start_date', 'pickup_time','end_date', 'dropoff_time')
        }),
        (_("Payment Information"), {  # Translated Section Title
            'fields': ('total_paid', 'total_cost', 'payment_status')
        }),
    )

    class Media:
        js = ('admin/js/calculate_total_cost.js',)
    def mark_as_picked_up(self, request, queryset):
        """ Admin action: Mark reservation as 'In Progress' and update pickup time. """
        for reservation in queryset:
            if reservation.status != "in_progress":
                reservation.pickup_time = now().time()
                reservation.status = "in_progress"
                reservation.car.is_available = False
                reservation.car.save(update_fields=['is_available'])
                reservation.save()

        self.message_user(request, _("The Vehicle Marked as Deliverd."))

    mark_as_picked_up.short_description = _("Mark as Delivred")

    def mark_as_returned(self, request, queryset):
        """ Admin action: Mark reservation as 'Completed' and update dropoff time. """
        for reservation in queryset:
            if reservation.status != "completed":
                reservation.dropoff_time = now().time()
                reservation.status = "completed"
                reservation.is_available = True
                reservation.car.is_available = True
                reservation.car.save(update_fields=['is_available'])
                reservation.save()
        self.message_user(request, _("The Vehicle Marked as Returned."))
        return JsonResponse({
            'show_popup': True
        })

    mark_as_returned.short_description = _("Mark as Returned")


    def pdf_link(self, obj):
        """Show a link to download the PDF in the admin interface."""
        if obj.pdf_receipt:
            return format_html('<a href="/media/{}" target="_blank">{}</a>', obj.pdf_receipt, _("Download Receipt"))
        return _("No PDF Available")

    pdf_link.short_description = _("PDF Receipt")

    def save_model(self, request, obj, form, change):
        """Override save to generate the PDF when the reservation is created or updated."""
        super().save_model(request, obj, form, change)
        obj.generate_pdf_receipt()

    def get_actions(self, request):
        """Override get_actions to remove default delete and use a custom delete action."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


### PAYMENT ADMIN ###
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'amount', 'payment_date')
    list_filter = ('payment_date',)  # Filter by payment date
    search_fields = ('reservation__car__plate_number', 'reservation__client__name')  # Search by car or client
    #readonly_fields = ('payment_date',)  # Prevent editing payment date
    actions = [custom_delete_selected]

    fieldsets = (
        (_('Payment Details'), {
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
    #readonly_fields = ('date',)  # Prevent editing the date
    actions = [custom_delete_selected]

    fieldsets = (
        (_('Expenditure Information'), {
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
    list_display = ('type', 'amount', 'date')
    list_filter = ('type',)
    search_fields = ('type',"date")

admin_site.register(User, UserAdmin)
admin_site.register(Car, CarAdmin)
admin_site.register(Client, ClientAdmin)
admin_site.register(Reservation, ReservationAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(CarExpenditure, CarExpenditureAdmin)
admin_site.register(Driver, DriverAdmin)
admin_site.register(BusinessExpenditure, BusinessExpenditureAdmin)
admin_site.register(ExpenditureType)