from django.contrib import admin
from .models import Car, Client, Reservation, CarExpenditure, Payment
from django.utils.html import format_html

### INLINE FOR EXPENDITURES IN CARS ###
class CarExpenditureInline(admin.TabularInline):
    model = CarExpenditure
    extra = 1  # Allows admin to add expenditures directly in the car interface
    readonly_fields = ('date',)  # Prevent editing the date


### CAR ADMIN ###
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'plate_number', 'year', 'image', 'daily_rate', 'total_expenditure')
    list_filter = ('year', 'daily_rate')  # Filter by car brand and year
    search_fields = ('plate_number', 'name')  # Search by plate number, brand, or model
    readonly_fields = ('total_expenditure',)  # Prevent editing total expenditure
    inlines = [CarExpenditureInline]  # Add expenditures inline

    fieldsets = (
        ('Car Information', {
            'fields': ('name', 'plate_number', 'year', 'image', 'daily_rate')
        }),
        ('Expenditure', {
            'fields': ('total_expenditure',)
        }),
    )


### CLIENT ADMIN ###
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'total_amount_paid', 'total_amount_due')
    search_fields = ('user__username', 'user__email', 'phone_number')  # Search by username, email, or phone
    readonly_fields = ('total_amount_paid', 'total_amount_due')  # Prevent editing payment info
    fieldsets = (
        ('Client Information', {
            'fields': ('user', 'phone_number', 'address')
        }),
        ('Payment Details', {
            'fields': ('total_amount_paid', 'total_amount_due')
        }),
    )


### INLINE FOR PAYMENTS IN RESERVATIONS ###
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1  # Allows admin to add payments directly in the reservation interface
    readonly_fields = ('payment_date',)  # Payment date is auto-filled


### RESERVATION ADMIN ###
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('car', 'client', 'start_date', 'end_date', 'total_cost', 'payment_status', 'initial_payment', 'pdf_link')
    list_filter = ('payment_status', 'start_date', 'end_date')  # Filter by payment status and rental period
    search_fields = ('car__plate_number', 'client__user__username', 'client__user__email')  # Search by car or client
    readonly_fields = ('total_cost', 'payment_status', 'pdf_link')  # Prevent editing calculated fields
    #inlines = [PaymentInline]  # Add payments inline
    fieldsets = (
        ('Reservation Details', {
            'fields': ('car', 'client', 'start_date', 'end_date')
        }),
        ('Payment Information', {
            'fields': ('initial_payment', 'total_cost', 'payment_status')
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


### PAYMENT ADMIN ###
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'amount', 'payment_date')
    list_filter = ('payment_date',)  # Filter by payment date
    search_fields = ('reservation__car__plate_number', 'reservation__client__user__username')  # Search by car or client
    readonly_fields = ('payment_date',)  # Prevent editing payment date

    fieldsets = (
        ('Payment Details', {
            'fields': ('reservation', 'amount', 'payment_date')
        }),
    )


### CAR EXPENDITURE ADMIN ###
@admin.register(CarExpenditure)
class CarExpenditureAdmin(admin.ModelAdmin):
    list_display = ('car', 'description', 'cost', 'date')
    list_filter = ('date',)  # Filter by expenditure date
    search_fields = ('car__plate_number', 'description')  # Search by car plate number or description
    readonly_fields = ('date',)  # Prevent editing the date

    fieldsets = (
        ('Expenditure Information', {
            'fields': ('car', 'description', 'cost', 'date')
        }),
    )
