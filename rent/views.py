from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, F, Q
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncMonth
from .models import Car, Reservation, Client, Payment, BusinessExpenditure, CarExpenditure
from django.http import JsonResponse
from django.utils.translation import get_language

def test(request):
    return render(request, 'test.html')

def home(request):
    cars = Car.objects.all()
    return render(request, 'home.html', {'cars': cars})


@staff_member_required
def admin_dashboard(request):
    # Get current date for reusable calculations
    current_date = now().date()

    # Monthly revenue and expenditure data
    monthly_revenue_data = Payment.objects.annotate(month=TruncMonth('payment_date')) \
        .values('month') \
        .annotate(total_revenue=Sum('amount')) \
        .order_by('month')

    monthly_car_expenditure_data = CarExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('cost'))

    monthly_business_expenditure_data = BusinessExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('amount'))

    # Combine expenditures
    monthly_expenditure_data = {}
    for item in monthly_car_expenditure_data:
        monthly_expenditure_data[item['month']] = item['total_expenditure']
    for item in monthly_business_expenditure_data:
        monthly_expenditure_data[item['month']] = monthly_expenditure_data.get(item['month'], 0) + item['total_expenditure']

    # Merge revenue and expenditure into a single list with profit
    monthly_financial_data = [
        {
            'month': revenue_item['month'],
            'revenue': revenue_item['total_revenue'],
            'expenditure': monthly_expenditure_data.get(revenue_item['month'], 0),
            'profit': revenue_item['total_revenue'] - monthly_expenditure_data.get(revenue_item['month'], 0),
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
        total_revenue = Payment.objects.filter(reservation__car=car).aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = CarExpenditure.objects.filter(car=car).aggregate(Sum('cost'))['cost__sum'] or 0
        profit = total_revenue - total_expense
        car_profit_data.append({
            'car': car,
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'profit': profit,
        })

    # Clients with balance due
    clients_with_due = Client.objects.filter(total_amount_due__gt=0)
    lang_code = get_language()  # Gets the current language code ('en', 'ar', etc.)
    context = {
        'monthly_financial_data': monthly_financial_data,
        'total_reservations': total_reservations,
        'available_cars': available_cars,
        'car_profit_data': car_profit_data,
        'clients_with_due': clients_with_due,
        'lang_code': lang_code
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