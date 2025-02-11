
from datetime import date, time, timedelta
from django.db import models
from django.forms import ValidationError
from django.utils.timezone import now
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from weasyprint import HTML
import os
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class Driver(models.Model):
    name = models.CharField(_("Name"), max_length=20, unique=True)  # Translated
    phone_number = models.CharField(
        _("Phone Number"), 
        max_length=15, 
        validators=[
            RegexValidator(r'^\+?\d{9,15}$', _("Enter a valid phone number."))
        ]
    )
    address = models.CharField(_("Address"), max_length=100)  # Translated default value
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    identity_card_number = models.CharField(
        _("Identity Card Number"), 
        max_length=20, 
        unique=True, 
        validators=[RegexValidator(r'^[A-Za-z0-9-]+$', _("Enter a valid ID card number."))]
    )
    driver_license_number = models.CharField(
        _("Driver's License Number"), 
        max_length=20, 
        unique=True, 
        validators=[RegexValidator(r'^[A-Za-z0-9-]+$', _("Enter a valid driver’s license number."))]
    )
    identity_card_front = models.ImageField(
        _("Identity Card Front"), upload_to='drivers/identity_cards/fronts/', blank=True, null=True
    )
    identity_card_back = models.ImageField(
        _("Identity Card Back"), upload_to='drivers/identity_cards/backs/', blank=True, null=True
    )
    driver_license_front = models.ImageField(
        _("Driver License Front"), upload_to='drivers/driver_licenses/fronts/', blank=True, null=True
    )
    driver_license_back = models.ImageField(
        _("Driver License Back"), upload_to='drivers/driver_licenses/backs/', blank=True, null=True
    )
    passport_image = models.ImageField(
        _("Passport Image"), upload_to='drivers/passports/', blank=True, null=True
    )
    def age(self):
        """Calculate the client's age based on their date of birth."""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    age.short_description = _("Age")
    class Meta:
        verbose_name = _("Driver")  # Sidebar translation
        verbose_name_plural = _("Drivers")  # Sidebar translation
    def __str__(self):
        return f"{self.name}"

class Car(models.Model):
    GEARBOX_CHOICES = [
        ('manual', _('Manual')),
        ('automatic', _('Automatic')),
        ('semi-automatic', _('Semi-Automatic')),
    ]
    
    FUEL_CHOICES = [
        ('petrol', _('Petrol')),
        ('diesel', _('Diesel')),
        ('electric', _('Electric')),
        ('hybrid', _('Hybrid')),
    ]
    brand = models.CharField(_("Brand"), max_length=20)
    model = models.CharField(_('Model'), max_length=20)
    plate_number = models.CharField(_('Registration Plate') , max_length=20, unique=True)
    image = models.ImageField(_('Image'), upload_to='cars/') 
    year = models.PositiveIntegerField(_('Year') ,default=2024)    
    gearbox = models.CharField(_('Transmission'),max_length=20, choices=GEARBOX_CHOICES, default='manual')
    fuel_type = models.CharField(_('Fuel Type'), max_length=20, choices=FUEL_CHOICES, default='Diesel')
    number_of_passengers = models.PositiveIntegerField(_('Number of passengers'), default=5)
    daily_rate = models.DecimalField(_('Daily Rate') ,max_digits=10, decimal_places=2, default=300)    
    total_expenditure = models.DecimalField(_('Total Expenditure'), max_digits=12, decimal_places=2, default=0.00)
    is_available = models.BooleanField(_("Available"), default=True)

    class Meta:
        verbose_name = _("Car") 
        verbose_name_plural = _("Cars")
    def get_total_expenditure(self):
        """
        Calculate the total expenditures for this car.
        """
        self.total_expenditure = self.expenditures.aggregate(total=models.Sum('cost'))['total'] or 0.00
        self.save(update_fields=['total_expenditure'])

    def delete(self, *args, **kwargs):
        """
        Override the delete method to handle cleanup.
        """
        # Delete related reservations and expenditures
        self.reservations.all().delete()
        self.expenditures.all().delete()

        # Delete the car's image from the filesystem
        if self.image:
            self.image.delete(save=False)

        # Call the original delete method
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.plate_number} ({_('Available') if self.is_available else _('Not Available')})"

class Client(models.Model):
    name = models.CharField(_("Name"), max_length=20, unique=True)  # Translated
    phone_number = models.CharField(
        _("Phone Number"), 
        max_length=15, 
        validators=[
            RegexValidator(r'^\+?\d{9,15}$', _("Enter a valid phone number."))
        ]
    )
    address = models.CharField(_("Address"), max_length=100)  # Translated default value
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    identity_card_number = models.CharField(
        _("Identity Card Number"), 
        max_length=20, 
        unique=True, 
        validators=[RegexValidator(r'^[A-Za-z0-9-]+$', _("Enter a valid ID card number."))]
    )
    driver_license_number = models.CharField(
        _("Driver's License Number"), 
        max_length=20, 
        unique=True, 
        validators=[RegexValidator(r'^[A-Za-z0-9-]+$', _("Enter a valid driver’s license number."))]
    )
    total_amount_paid = models.DecimalField(
        _("Total Amount Paid"), max_digits=12, decimal_places=2, default=0.00
    )
    total_amount_due = models.DecimalField(
        _("Total Amount Due"), max_digits=12, decimal_places=2, default=0.00
    )
    
    identity_card_front = models.ImageField(
        _("Identity Card Front"), upload_to='clients/identity_cards/fronts/', blank=True, null=True
    )
    identity_card_back = models.ImageField(
        _("Identity Card Back"), upload_to='clients/identity_cards/backs/', blank=True, null=True
    )
    driver_license_front = models.ImageField(
        _("Driver License Front"), upload_to='clients/driver_licenses/fronts/', blank=True, null=True
    )
    driver_license_back = models.ImageField(
        _("Driver License Back"), upload_to='clients/driver_licenses/backs/', blank=True, null=True
    )
    passport_image = models.ImageField(
        _("Passport Image"), upload_to='clients/passports/', blank=True, null=True
    )

    rating = models.PositiveSmallIntegerField(
        _("Client Rating"),
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Rating of the client (1 to 5)"),
    )

    class Meta:
        verbose_name = _("Client")  # Sidebar translation
        verbose_name_plural = _("Clients")

    def __str__(self):
        return f"{self.name} - {self.rating}"
    
    def age(self):
        """Calculate the client's age based on their date of birth."""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    age.short_description = _("Age")


    def update_payment_info(self):
        """
        Update the total amount paid and due for this client.
        """
        # Calculate total paid and total due based on all reservations
        self.total_amount_paid = sum(
            sum(payment.amount for payment in reservation.payments.all()) for reservation in self.reservations.all()
        )
        self.total_amount_due = sum(
            reservation.total_cost for reservation in self.reservations.all()
        ) - self.total_amount_paid
        self.save(update_fields=['total_amount_paid', 'total_amount_due'])



class Reservation(models.Model):
    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
    ]
    car = models.ForeignKey(
        "Car", on_delete=models.CASCADE, related_name='reservations', verbose_name=_("Car")
    )
    client = models.ForeignKey(
        "Client", on_delete=models.CASCADE, related_name='reservations', verbose_name=_("Client")
    )
    drivers = models.ManyToManyField(
        "Driver", blank=True, related_name='reservations', verbose_name=_("Drivers")
    )  # Multiple drivers allowed
    
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    pickup_time = models.TimeField(_("Pickup Time"), default=time(12, 0))  # Default 12:00 PM
    dropoff_time = models.TimeField(_("Dropoff Time"), default=time(12, 0))  # Default 12:00 PM
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default="pending")
    actual_daily_rate = models.DecimalField(_('Actual Daily Rate'), max_digits=10, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(
        _("Total Cost"), max_digits=12, decimal_places=2, blank=True
    )  # Calculated cost for reservation
    
    PAYMENT_STATUS_CHOICES = [
        ('Paid', _("Paid")),
        ('Partially Paid', _("Partially Paid")),
        ('Unpaid', _("Unpaid")),
    ]
    
    payment_status = models.CharField(
        _("Payment Status"), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Unpaid'
    )
    
    total_paid = models.DecimalField(
        _("Total Paid"), max_digits=12, decimal_places=2, default=0.00
    )  # Tracks total payments made
    
    pdf_receipt = models.FileField(
        _("PDF Receipt"), upload_to='reservations/pdfs/', blank=True, null=True
    )
    class Meta:
        verbose_name = _("Reservation")  # Sidebar translation
        verbose_name_plural = _("Reservations")

    @property
    def rental_days(self):
        return (self.end_date - self.start_date).days if self.start_date and self.end_date else 0
    def clean(self):
        today = now().date()

        # 🔥 1. Prevent start dates in the past (unless marking as completed)
        if self.start_date < today and self.status != "completed":
            raise ValidationError(_("Reservation start date cannot be in the past unless it is marked as completed."))

        # 🔥 2. Prevent end_date from being before start_date
        if self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before the start date."))

        # 🔥 3. Check for overlapping reservations
        overlapping_reservations = Reservation.objects.filter(
            car=self.car,
            end_date__gt=self.start_date,  # 🔥 Fixed: Allow starting **on** the same day another reservation ends
            start_date__lt=self.end_date,  # 🔥 Fixed: Allow ending **on** the same day another reservation starts
        ) 

        if self.pk:  # Exclude the current instance if it's being updated
            overlapping_reservations = overlapping_reservations.exclude(pk=self.pk)

        if overlapping_reservations.exists():
            raise ValidationError(_("This car is already reserved for the selected dates."))

        # 🔥 4. Auto-update status for today's reservations
        if self.start_date == today:
            self.status = "in_progress"
            self.car.is_available = False

        super().clean()

    def generate_pdf_receipt(self):
        """
        Generate a PDF receipt for the reservation.
        """
        # Render the HTML template with context
        context = {
            'reservation': self,
            'now': now(),
            'company_name': 'TWINS T.B CAR',
            'company_logo': '/path/to/logo.png',
        }
        
        html_content = render_to_string('reservation_pdf.html', context)

        # Generate the PDF file
        pdf_path = f'media/reservations/pdfs/reservation_{self.pk}.pdf'
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        HTML(string=html_content).write_pdf(pdf_path)

        # Save the PDF file path to the model
        self.pdf_receipt = f'reservations/pdfs/reservation_{self.pk}.pdf'

    def __str__(self):
        return f"{_("Reservation")} {self.pk}: {self.client.name} - {self.car.plate_number}"

    def calculate_total_cost(self):
        """
        Calculate total cost of the reservation based on the rental period.
        """
        rental_days = (self.end_date - self.start_date).days
        return rental_days * self.actual_daily_rate

    def update_payment_status(self):
        """
        Update the payment status of this reservation based on its payments.
        """
        if self.total_paid >= self.total_cost:
            self.payment_status = 'Paid'
        elif self.total_paid > 0:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Unpaid'
        self.save(update_fields=['payment_status'])

    def save(self, *args, **kwargs):
        if self.actual_daily_rate is None:  # Set default only if not provided
            self.actual_daily_rate = self.car.daily_rate
        self.total_cost = self.calculate_total_cost()
        old_instance = Reservation.objects.filter(pk=self.pk).first()
        if not old_instance or old_instance.start_date != self.start_date or old_instance.end_date != self.end_date or old_instance.car != self.car:
            self.total_cost = self.calculate_total_cost()

        # Check if this is the first save (before generating PDF)
        print(self.start_date == now().date())
        if self.start_date == now().date() and not old_instance:
            self.status = "in_progress"
            self.pickup_time = now().time()
            self.car.is_available = False
            self.car.save(update_fields=['is_available'])
        super().save(*args, **kwargs)
        self.client.update_payment_info()
        '''if not self.pdf_receipt or (
            old_instance
            and (
                old_instance.start_date != self.start_date
                or old_instance.end_date != self.end_date
                or old_instance.car != self.car
            )
        ):'''
        self.generate_pdf_receipt()
        Reservation.objects.filter(pk=self.pk).update(pdf_receipt=self.pdf_receipt)

    
    def delete(self, *args, **kwargs):
        self.car.is_available = True
        self.car.save(update_fields=['is_available'])
        super().delete(*args, **kwargs)
        self.client.update_payment_info()


class CarExpenditure(models.Model):
    car = models.ForeignKey(
        "Car", on_delete=models.CASCADE, related_name='expenditures', verbose_name=_("Car")
    )
    description = models.CharField(_("Description"), max_length=50)
    cost = models.DecimalField(_("Cost"), max_digits=12, decimal_places=2)
    date = models.DateField(_("Date"), default=now)

    class Meta:
        verbose_name = _("Car Expenditure")  # Sidebar translation
        verbose_name_plural = _("Car Expenditures")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.car.get_total_expenditure()        

    def delete(self, *args, **kwargs):
        # Call the original delete method
        super().delete(*args, **kwargs)
        self.car.get_total_expenditure()  

    def __str__(self):
        return f"{_("Car Expenditure")} {self.car.plate_number}: {self.description} - {self.cost}"

class Payment(models.Model):
    reservation = models.ForeignKey(
        "Reservation", on_delete=models.CASCADE, related_name='payments', verbose_name=_("Reservation")
    )
    amount = models.DecimalField(_("Amount Paid"), max_digits=12, decimal_places=2)
    payment_date = models.DateField(_("Payment Date"), default=now)
    class Meta:
        verbose_name = _("Payment")  # Sidebar translation
        verbose_name_plural = _("Payments")
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.reservation.total_paid = sum(payment.amount for payment in self.reservation.payments.all())
        self.reservation.save(update_fields=['total_paid'])
        self.reservation.update_payment_status()
        self.reservation.client.update_payment_info()

    def delete(self, *args, **kwargs):
        """
        Override the delete method to update reservation's and client's payment statuses.
        """
        # Subtract this payment's amount from the reservation's total_paid
        self.reservation.total_paid -= self.amount        
        self.reservation.save(update_fields=['total_paid'])

        # Update the reservation's payment status
        self.reservation.update_payment_status()

        # Update the client's payment info
        # Call the original delete method
        super().delete(*args, **kwargs)
        self.reservation.client.update_payment_info()

    def __str__(self):
        return f"{_('Payment')} {self.pk}: {self.amount}"

class BusinessExpenditure(models.Model):
    type = models.ForeignKey("ExpenditureType", on_delete=models.CASCADE, related_name='BusinessExpenditures', verbose_name=_("Type"))
    amount = models.DecimalField(_("Amount"), max_digits=12, decimal_places=2)  # Cost
    date = models.DateField(_("Date"), auto_now_add=True)  # Expenditure date
    class Meta:
        verbose_name = _("Business Expenditure")  # Sidebar translation
        verbose_name_plural = _("Business Expenditures")
    def __str__(self):
        return f"{self.type} - {self.amount}"

class ExpenditureType(models.Model): 




    type = models.CharField(_("Type"), max_length=20)
    class Meta:
        verbose_name = _("Expenditures Type") 
        verbose_name_plural = _("Expenditures Types")
    def __str__(self):
        return self.type




class CustomerInfo(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
