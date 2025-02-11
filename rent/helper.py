from django.db.models import Sum, F
from django.db.models.functions import TruncMonth
from datetime import timedelta
from calendar import monthrange

def calculate_rental_days_for_months(start_date, end_date):
    """
    Calculate the number of rental days for each month between start_date and end_date
    :param start_date: The start date of the reservation.
    :param end_date: The end date of the reservation.
    :return: A list of dictionaries with the 'month' and 'rental_days' for each month.
    """
    rental_days_by_month = []
    
    # We need to iterate through each month between the start and end date
    current_date = start_date
    
    while current_date <= end_date:
        # Get the first day of the current month
        first_day_of_month = current_date.replace(day=1)
        
        # Get the last day of the current month
        _, last_day_of_month = monthrange(current_date.year, current_date.month)
        last_day_of_month = current_date.replace(day=last_day_of_month)

        # Calculate the rental days for the current month
        month_start = max(current_date, first_day_of_month)
        month_end = min(end_date, last_day_of_month)
        
        # Calculate the rental days in this month
        rental_days = (month_end - month_start).days + 1
        
        if rental_days > 0:
            rental_days_by_month.append({
                'month': month_start,
                'rental_days': rental_days
            })
        
        # Move to the next month
        current_date = month_end + timedelta(days=1)
    
    return rental_days_by_month

# Now, calculate the rental days per month for each reservation