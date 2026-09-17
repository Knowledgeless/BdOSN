from django import template
import calendar
import datetime


register = template.Library()

@register.filter(name="get_month_days")
def get_month_days(value, month_year):
    """
    Example: {% for day in 1|get_month_days:month_year %}
    Returns a range of all days in the given month and year.
    """
    try:
        month, year = month_year
        return range(1, calendar.monthrange(year, month)[1] + 1)
    except Exception:
        return []

@register.filter(name="day_has_booking")
def day_has_booking(bookings, day):
    """Check if any booking exists for the given day."""
    return any(b.conference_date.day == day for b in bookings)

@register.filter(name="bookings_for_day")
def bookings_for_day(bookings, day):
    """Return all bookings for the given day."""
    return [b for b in bookings if b.conference_date.day == day]



@register.filter
def get_month_start_blank(value, month_year):
    """
    Returns the number of empty cells before the first day of the month.
    Usage: {% for blank in 1|get_month_start_blank:month_year %}
    month_year = (month, year)
    """
    try:
        month, year = month_year
        first_day = datetime.date(year, month, 1)
        # Python weekday(): Monday=0, Sunday=6
        # We want Sunday=0, Saturday=6 for calendar grid
        return range((first_day.weekday() + 1) % 7)
    except Exception:
        return []
    
# BOOKING_COLORS = ['#0d6efd', '#6f42c1', '#198754', '#fd7e14', '#dc3545', '#0dcaf0']

# @register.filter(name="bookings_for_day_with_colors_modal")
# def bookings_for_day_with_colors_modal(bookings, day):
#     """
#     Return all bookings for a given day with a color assigned for modal view.
#     Each day starts cycling colors independently.
#     """
#     day_bookings = [b for b in bookings if b.conference_date.day == day]
#     for i, booking in enumerate(day_bookings):
#         booking.color = BOOKING_COLORS[i % len(BOOKING_COLORS)]
#     return day_bookings

