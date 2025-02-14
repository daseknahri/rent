from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, F, Q
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncMonth

from rent.helper import calculate_rental_days_for_months
from .models import Car, Reservation, Client, Payment, BusinessExpenditure, CarExpenditure, CustomerInfo
from django.http import JsonResponse
from django.utils.translation import get_language
from collections import defaultdict


def thank_you(request):
    return render(request, 'thank_you.html')


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        city = request.POST.get('city')
        phone = request.POST.get('phone')

        # Save data to the database
        CustomerInfo.objects.create(name=name, city=city, phone=phone)

        # Redirect to thank you page
        return redirect('thank_you')

    return render(request, 'home.html')

def home(request):
    cars = Car.objects.all()
    return render(request, 'home.html', {'cars': cars})


@staff_member_required
def admin_dashboard(request):
    # Get current date for reusable calculations
    current_date = now().date()

    # Monthly revenue and expenditure data
    from collections import defaultdict

# Initialize dictionary to store revenue per month
    monthly_revenue_data = defaultdict(float)

# Iterate through reservations
    for reservation in Reservation.objects.all():
        start_date = reservation.start_date
        end_date = reservation.end_date
        daily_rate = reservation.actual_daily_rate or reservation.car.daily_rate

        # Split rental days across months
        while start_date < end_date:
            month = start_date.replace(day=1)

            # Determine the last day of the current month
            last_day_of_month = (month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Calculate rental days in this month
            days_in_month = (min(end_date, last_day_of_month) - start_date).days + 1
            monthly_revenue_data[month] += days_in_month * float(daily_rate)

            # Move to the next month
            start_date = last_day_of_month + timedelta(days=1)

    # Convert to list format for sorting
    monthly_revenue_data = [{'month': month, 'total_revenue': revenue} for month, revenue in monthly_revenue_data.items()]
    monthly_revenue_data.sort(key=lambda x: x['month'])

    # Calculate expenditures (keeping your original logic)
    monthly_car_expenditure_data = CarExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('cost'))

    monthly_business_expenditure_data = BusinessExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('amount'))

    # Merge expenditures
    monthly_expenditure_data = defaultdict(float)
    for item in monthly_car_expenditure_data:
        monthly_expenditure_data[item['month']] += item['total_expenditure']
    for item in monthly_business_expenditure_data:
        monthly_expenditure_data[item['month']] += item['total_expenditure']

    # Merge revenue and expenditure into financial data
    monthly_financial_data = [
        {
            'month': revenue_item['month'],
            'revenue': revenue_item['total_revenue'],
            'expenditure': monthly_expenditure_data[revenue_item['month']],
            'profit': revenue_item['total_revenue'] - monthly_expenditure_data[revenue_item['month']],
        }
        for revenue_item in monthly_revenue_data
    ]

    # Sort by month
    monthly_financial_data.sort(key=lambda x: x['month'])

    # Number of reservations and available cars
    total_reservations = Reservation.objects.count()
    available_cars = Car.objects.filter(is_available=True).count()

    # Total profit and expenses by car
    car_profit_data = []

    for car in Car.objects.all():
        # Calculate total revenue using reservation days * actual daily rate
        total_revenue = sum(
            reservation.rental_days * (reservation.actual_daily_rate or car.daily_rate)
            for reservation in car.reservations.all()
        )

        # Calculate total expenditure for the car
        total_expense = CarExpenditure.objects.filter(car=car).aggregate(Sum('cost'))['cost__sum'] or 0

        # Calculate profit
        profit = total_revenue - total_expense

        # Append data
        car_profit_data.append({
            'car': car,
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'profit': profit,
        })

    # Clients with balance due
    clients_with_due = Client.objects.filter(total_amount_due__gt=0)

    # Car rental days for each month
    car_rental_days_data = []
    for car in Car.objects.all():
        rental_days_by_month = {}
        for reservation in car.reservations.all():
            start_date = reservation.start_date
            end_date = reservation.end_date

            # Split reservation into months
            while start_date < end_date:
                month = start_date.replace(day=1)
                
                # Determine the last day of the current month
                last_day_of_month = (month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                # Calculate the days in the current month
                days_in_month = (min(end_date, last_day_of_month) - start_date).days + 1
                rental_days_by_month[month] = rental_days_by_month.get(month, 0) + days_in_month
                
                # Move to the next month
                start_date = last_day_of_month + timedelta(days=1)

        # Append data
        car_rental_days_data.append({
            'car': car,
            'rental_days_by_month': rental_days_by_month,
        })

    context = {
        'monthly_financial_data': monthly_financial_data,
        'total_reservations': total_reservations,
        'available_cars': available_cars,
        'car_profit_data': car_profit_data,
        'clients_with_due': clients_with_due,
        'car_rental_days_data': car_rental_days_data,
        'lang_code': get_language()
    }
    return context



def get_car_daily_rate(request):
    """Return the daily rental rate of the selected car."""
    car_id = request.GET.get('car_id')
    if not car_id:
        return JsonResponse({"error": "Car ID not provided"}, status=400)

    try:
        car = Car.objects.get(id=car_id)
        return JsonResponse({"daily_rate": float(car.daily_rate)})
    except Car.DoesNotExist:
        return JsonResponse({"error": "Car not found"}, status=404)