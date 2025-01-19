
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

from django.template.loader import render_to_string
from weasyprint import HTML
import os

class Car(models.Model):
    """
    Represents a car in the system.
    """
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
    year = models.PositiveIntegerField(default=2020)    
    gearbox = models.CharField(max_length=20, choices=GEARBOX_CHOICES, default='manual')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='Diesel')
    passenger = models.PositiveIntegerField(default=5)
    description = models.TextField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)    
    total_expenditure = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) 

    def __str__(self):
        return f"{self.name} ({self.plate_number})"

class Client(models.Model):
    """
    Represents a client who rents cars.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')  # Using the built-in User model
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Total paid by the client
    total_amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Remaining balance to pay

    def __str__(self):
        return f"{self.user.username}"

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
        self.save()

class Reservation(models.Model):
    """
    Represents a car reservation.
    """
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reservations')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reservations')
    start_date = models.DateField()
    end_date = models.DateField()
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True)  # Calculated cost for the reservation
    payment_status = models.CharField(max_length=20, choices=[
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Unpaid', 'Unpaid')], default='Unpaid')
    initial_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Initial payment made during reservation")
    pdf_receipt = models.FileField(upload_to='reservations/pdfs/', blank=True, null=True)

    def generate_pdf_receipt(self):
        """
        Generate a PDF receipt for the reservation.
        """
        # Render the HTML template with context
        context = {
            'reservation': self,
            'now': now(),
        }
        html_content = render_to_string('reservation_pdf.html', context)

        # Generate the PDF file
        pdf_path = f'media/reservations/pdfs/reservation_{self.pk}.pdf'
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        HTML(string=html_content).write_pdf(pdf_path)

        # Save the PDF file path to the model
        self.pdf_receipt = f'reservations/pdfs/reservation_{self.pk}.pdf'

    def __str__(self):
        return f"Reservation {self.pk}: {self.client.user.get_full_name()} - {self.car}"

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
        total_paid = sum(payment.amount for payment in self.payments.all())
        if total_paid >= self.total_cost:
            self.payment_status = 'Paid'
        elif total_paid > 0:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Unpaid'
        self.save()

    def save(self, *args, **kwargs):
        """
        Override the save method to calculate the total cost and handle initial payment logic.
        """
        # Calculate the total cost of the reservation
        self.total_cost = self.calculate_total_cost()

        # Check if this is the first save (before generating PDF)
        is_new_instance = not self.pk

        super().save(*args, **kwargs)

        # Generate the PDF receipt after saving (only for new instances)
        if is_new_instance and not self.pdf_receipt:
            self.generate_pdf_receipt()
            # Save the PDF path only (to avoid recursion)
            super().save(update_fields=['pdf_receipt'])

        # Handle the initial payment logic
        if self.initial_payment > 0 and is_new_instance:
            self.payment_status = 'Partially Paid'
            if self.initial_payment == self.total_cost:
                self.payment_status = 'Paid'

            # Create a Payment object only if initial_payment is greater than 0
            Payment.objects.create(
                reservation=self,
                amount=self.initial_payment,
                payment_date=now()
            )

        # Update the client's payment info after saving the reservation
        self.client.update_payment_info()


class CarExpenditure(models.Model):
    """
    Tracks expenditure for each car (e.g., maintenance, repairs).
    """
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='expenditures')
    description = models.TextField()
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=now)

    def save(self, *args, **kwargs):
        """
        Override the save method to update the total expenditure of the car.
        """
        super().save(*args, **kwargs)
        self.car.total_expenditure += self.cost
        self.car.save()

    def __str__(self):
        return f"Expenditure on {self.car}: {self.description} - {self.cost}"

class Payment(models.Model):
    """
    Tracks payments made by clients for reservations.
    """
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=now)

    def save(self, *args, **kwargs):
        """
        Override the save method to update the reservation's and client's payment statuses.
        """
        super().save(*args, **kwargs)
        # Update the reservation's payment status whenever a new payment is made
        self.reservation.update_payment_status()
        # Update the client's payment info
        self.reservation.client.update_payment_info()

    def __str__(self):
        return f"Payment {self.pk}: {self.amount} for Reservation {self.reservation.pk}"
