from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count, F, Q
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncMonth
from .models import Car, Reservation, Client, Payment, BusinessExpenditure, CarExpenditure

def home(request):
    cars = Car.objects.all()
    return render(request, 'home.html', {'cars': cars})

@staff_member_required
def admin_dashboard(request):
    # Get current date for reusable calculations
    current_date = now().date()

    # Monthly revenue
    monthly_revenue_data = Payment.objects.annotate(month=TruncMonth('payment_date')) \
        .values('month') \
        .annotate(total_revenue=Sum('amount')) \
        .order_by('month')

    # Monthly car expenditures
    monthly_car_expenditure_data = CarExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('cost'))

    # Monthly business expenditures
    monthly_business_expenditure_data = BusinessExpenditure.objects.annotate(month=TruncMonth('date')) \
        .values('month') \
        .annotate(total_expenditure=Sum('amount'))

    # Combine expenditures
    monthly_expenditure_data = {}
    for item in monthly_car_expenditure_data:
        month = item['month']
        monthly_expenditure_data[month] = monthly_expenditure_data.get(month, 0) + item['total_expenditure']
    for item in monthly_business_expenditure_data:
        month = item['month']
        monthly_expenditure_data[month] = monthly_expenditure_data.get(month, 0) + item['total_expenditure']

    # Merge revenue and expenditure into a single list with profit
    monthly_financial_data = []
    for revenue_item in monthly_revenue_data:
        month = revenue_item['month']
        revenue = revenue_item['total_revenue']
        expenditure = monthly_expenditure_data.get(month, 0)
        profit = revenue - expenditure

        monthly_financial_data.append({
            'month': month,
            'revenue': revenue,
            'expenditure': expenditure,
            'profit': profit,
        })

    # Sort the data by month
    monthly_financial_data.sort(key=lambda x: x['month'])

    # Pass data to the template
    context = {
        'monthly_financial_data': monthly_financial_data,
    }
    return context


    '''
    # Calculate total revenue from all reservations
    total_revenue = Reservation.objects.aggregate(
        total_revenue=Sum('total_cost')
    )['total_revenue'] or 0

    # Count total reservations
    total_reservations = Reservation.objects.count()

    # Count total available cars (cars without active reservations)
    total_available_cars = Car.objects.filter(
        ~Q(reservations__end_date__gte=now().date())
    ).distinct().count()

    # Count total clients
    total_clients = Client.objects.count()

    # Monthly revenue for the last 6 months
    six_months_ago = now().date() - timedelta(days=180)
    monthly_revenue = (
        Reservation.objects.filter(start_date__gte=six_months_ago)
        .annotate(month=F('start_date__month'))
        .values('month')
        .annotate(revenue=Sum('total_cost'))
        .order_by('month')
    )

    # Ensure monthly revenue contains all months (optional logic)
    monthly_revenue_data = {entry['month']: entry['revenue'] for entry in monthly_revenue}
    months = [(six_months_ago.month + i) % 12 + 1 for i in range(6)]  # Generate last 6 months
    full_monthly_revenue = [
        {'month': month, 'revenue': monthly_revenue_data.get(month, 0)} for month in months
    ]

    # Context for rendering
    context = {
        'total_revenue': total_revenue,
        'total_reservations': total_reservations,
        'total_available_cars': total_available_cars,
        'total_clients': total_clients,
        'monthly_revenue': full_monthly_revenue,
    }
    return context
'''