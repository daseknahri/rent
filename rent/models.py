
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.forms import ValidationError
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.core.mail import send_mail

from django.template.loader import render_to_string
from weasyprint import HTML
import os
from decimal import Decimal
from django.db.models.functions import Lower


class Driver(models.Model):
    name = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=100, default='TANGER ')
    identity_card_image = models.ImageField(upload_to='clients/identity_cards/', blank=True, null=True)
    driver_license_image = models.ImageField(upload_to='clients/driver_licenses/', blank=True, null=True)
    passport_image = models.ImageField(upload_to='clients/passports/', blank=True, null=True)
    def __str__(self):
        return f"{self.name}"

class Car(models.Model):
    GEARBOX_CHOICES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('semi-automatic', 'Semi-Automatic'),
    ]
    
    FUEL_CHOICES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]
    name = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=20, unique=True)
    image = models.ImageField(upload_to='cars/') 
    year = models.PositiveIntegerField(default=2024)    
    gearbox = models.CharField(max_length=20, choices=GEARBOX_CHOICES, default='manual')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='Diesel')
    passenger = models.PositiveIntegerField(default=5)
    description = models.CharField(max_length=50)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=300)    
    total_expenditure = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

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

    @property
    def is_available(self):
        # Check if the car has any active reservations
        return not self.reservations.filter(end_date__gte=now().date()).exists()

    def __str__(self):
        return f"{self.name} ({self.plate_number}) - {'Available' if self.is_available else 'Rented'}"

class Client(models.Model):
    name = models.CharField(max_length=20, unique=True)  # Using the built-in User model
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=100, default='TANGER ')
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Total paid by the client
    total_amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Remaining balance to pay
    identity_card_image = models.ImageField(upload_to='clients/identity_cards/', blank=True, null=True)
    driver_license_image = models.ImageField(upload_to='clients/driver_licenses/', blank=True, null=True)
    passport_image = models.ImageField(upload_to='clients/passports/', blank=True, null=True)
    rating = models.PositiveSmallIntegerField(default=0,help_text="Rating of the client (1 to 5)",)
    def __str__(self):
        return f"{self.name} - {self.rating}"

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
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reservations')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reservations')
    drivers = models.ManyToManyField(Driver, blank=True, related_name='reservations')  # Add multiple drivers
    start_date = models.DateField()
    end_date = models.DateField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True)  # Calculated cost for the reservation
    payment_status = models.CharField(max_length=20, choices=[
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Unpaid', 'Unpaid')], default='Unpaid')
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Tracks total payments made
    pdf_receipt = models.FileField(upload_to='reservations/pdfs/', blank=True, null=True)

    def clean(self):
        if self.start_date < now().date():
            raise ValidationError("Reservation start date cannot be in the past.")
        overlapping_reservations = Reservation.objects.filter(
            car=self.car,
            end_date__gte=self.start_date,
            start_date__lte=self.end_date,
        )
        if self.pk:  # Exclude the current instance if it's being updated
            overlapping_reservations = overlapping_reservations.exclude(pk=self.pk)

        if overlapping_reservations.exists():
            raise ValidationError("This car is already reserved for the selected dates.")
        super().clean()

    def generate_pdf_receipt(self):
        """
        Generate a PDF receipt for the reservation.
        """
        # Render the HTML template with context
        context = {
            'reservation': self,
            'now': now(),
            'company_name': 'Your Company Name',
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
        return f"Reservation {self.pk}: {self.client.name} - {self.car}"

    def calculate_total_cost(self):
        """
        Calculate total cost of the reservation based on the rental period.
        """
        rental_days = (self.end_date - self.start_date).days
        return rental_days * self.car.daily_rate

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
        # Calculate the total cost of the reservation
        self.total_cost = self.calculate_total_cost()
        old_instance = Reservation.objects.filter(pk=self.pk).first()
        if not old_instance or old_instance.start_date != self.start_date or old_instance.end_date != self.end_date or old_instance.car != self.car:
            self.total_cost = self.calculate_total_cost()

        # Check if this is the first save (before generating PDF)

        super().save(*args, **kwargs)
        self.client.update_payment_info()

        if not self.pdf_receipt or (
            old_instance
            and (
                old_instance.start_date != self.start_date
                or old_instance.end_date != self.end_date
                or old_instance.car != self.car
            )
        ):
            self.generate_pdf_receipt()
            # Save only the updated pdf_receipt field to avoid recursion
            Reservation.objects.filter(pk=self.pk).update(pdf_receipt=self.pdf_receipt)
        send_mail(
            'Reservation Confirmation',
            f'Dear {self.client.name}, your reservation for {self.car} is confirmed.',
            'noreply@example.com',
            [self.client.name],
            fail_silently=True,
        )

    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.client.update_payment_info()

class CarExpenditure(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='expenditures')
    description = models.CharField(max_length=50)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=now)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.car.get_total_expenditure()        

    def delete(self, *args, **kwargs):
        # Call the original delete method
        super().delete(*args, **kwargs)
        self.car.get_total_expenditure()  

    def __str__(self):
        return f"Expenditure on {self.car}: {self.description} - {self.cost}"

class Payment(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=now)

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
        return f"Payment {self.pk}: {self.amount} for Reservation {self.reservation.pk}"

class BusinessExpenditure(models.Model):
    description = models.CharField(max_length=100)  # Example: "Office rent"
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Cost
    date = models.DateField(auto_now_add=True)  # Expenditure date

    def __str__(self):
        return f"{self.description} - {self.amount}"