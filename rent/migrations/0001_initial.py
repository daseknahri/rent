# Generated by Django 5.1.4 on 2025-01-15 22:06

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Car',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('plate_number', models.CharField(max_length=20, unique=True)),
                ('image', models.ImageField(upload_to='cars/')),
                ('year', models.PositiveIntegerField(default=2020)),
                ('gearbox', models.CharField(choices=[('manual', 'Manual'), ('automatic', 'Automatic'), ('semi-automatic', 'Semi-Automatic')], default='manual', max_length=20)),
                ('fuel_type', models.CharField(choices=[('petrol', 'Petrol'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], default='petrol', max_length=20)),
                ('passenger', models.PositiveIntegerField(default=5)),
                ('description', models.TextField()),
                ('daily_rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_expenditure', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
            ],
        ),
        migrations.CreateModel(
            name='CarExpenditure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('cost', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenditures', to='rent.car')),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15)),
                ('address', models.TextField()),
                ('total_amount_paid', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('total_amount_due', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12)),
                ('payment_status', models.CharField(choices=[('Paid', 'Paid'), ('Partially Paid', 'Partially Paid'), ('Unpaid', 'Unpaid')], default='Unpaid', max_length=20)),
                ('initial_payment', models.DecimalField(decimal_places=2, default=0.0, help_text='Initial payment made during reservation', max_digits=12)),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='rent.car')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='rent.client')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_date', models.DateField(default=django.utils.timezone.now)),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='rent.reservation')),
            ],
        ),
    ]
