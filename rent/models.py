# Create your models here.
from django.db import models

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
    image = models.ImageField(upload_to='cars/') 
    year = models.PositiveIntegerField(default=2020)    
    gearbox = models.CharField(max_length=20, choices=GEARBOX_CHOICES, default='manual')
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol')
    passenger = models.PositiveIntegerField(default=5)
    description = models.TextField()
    prix = models.PositiveIntegerField(default=250)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.car.name} reservation in {self.city}"
