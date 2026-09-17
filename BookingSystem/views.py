from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from datetime import datetime, date, time as dt_time
from .models import Room, Booking, ArchivedBooking
from .forms import BookingForm, CustomLoginForm
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.decorators.http import require_GET
from calendar import monthrange, month_name
from django.utils.timezone import localdate
import calendar

ORGANIZATIONS = [
    "SPSB", "BdMSO", "BdOSN", "WROBd", "IROC",
    "Malala Project", "BdMO", "Other",
]

BOOKING_COLORS = ['#fd7e14', "#842bff", '#0dcaf0', '#dc3545','#0d6efd', '#198754',]

def home(request):
    rooms = Room.objects.all()
    today = datetime.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])

    bookings = list(
        Booking.objects.filter(
            conference_date__range=(start_date, end_date)
        ).order_by('conference_date', 'start_time')
    )

    # Group bookings by day
    bookings_by_day = {}
    for booking in bookings:
        day = booking.conference_date.day
        if day not in bookings_by_day:
            bookings_by_day[day] = []
        bookings_by_day[day].append(booking)

    # Assign colors independently per day
    for day, day_bookings in bookings_by_day.items():
        for i, booking in enumerate(day_bookings):
            booking.color = BOOKING_COLORS[i % len(BOOKING_COLORS)]

    months = [(i, month_name[i]) for i in range(1, 13)]

    context = {
        'rooms': rooms,
        'bookings': bookings,
        'bookings_by_day': bookings_by_day,  # ✅ pass grouped bookings with colors
        'selected_month': month,
        'selected_year': year,
        'months': months,
        'years': range(today.year, today.year + 3),
        'month_year': (month, year),
    }
    return render(request, "home.html", context)



@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    bookings = Booking.objects.filter(room=room).order_by('conference_date', 'start_time')

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        additional_support = request.POST.get("additional_support", "").strip()
        organization = request.POST.get("organization", "").strip()
        booked_for = request.POST.get("booked_for", "").strip()

        dates = request.POST.getlist("conference_date[]")
        start_times = request.POST.getlist("start_time[]")
        end_times = request.POST.getlist("end_time[]")

        if not dates or not start_times or not end_times:
            messages.error(request, "Please provide at least one booking slot.")
            return redirect('book_room', room_id=room.id)

        created_count = 0
        for idx, (d, s, e) in enumerate(zip(dates, start_times, end_times), start=1):
            if not (d and s and e):
                messages.warning(request, f"Skipping empty slot #{idx}.")
                continue

            try:
                booking_date = datetime.strptime(d, "%Y-%m-%d").date()
                start = datetime.strptime(s, "%H:%M").time()
                end = datetime.strptime(e, "%H:%M").time()
            except ValueError:
                messages.error(request, f"Invalid date/time format in slot #{idx}.")
                continue

            if start >= end:
                messages.error(request, f"Invalid time range on {booking_date} (slot #{idx}).")
                continue

            if start < dt_time(9, 0) or end > dt_time(22, 0):
                messages.error(request, f"Booking on {booking_date} must be between 09:00 and 22:00.")
                continue

            if booking_date < localdate():
                messages.error(request, f"Invalid date {booking_date} (slot #{idx}): cannot book past dates.")
                continue

            clash_exists = Booking.objects.filter(
                room=room,
                conference_date=booking_date,
                start_time__lt=end,
                end_time__gt=start
            ).exists()

            if clash_exists:
                messages.error(request, f"Time clash on {booking_date} (slot #{idx}) {s}-{e}.")
                continue

            Booking.objects.create(
                user=request.user,
                room=room,
                title=title or "Untitled Conference",
                conference_date=booking_date,
                start_time=start,
                end_time=end,
                organization=organization or None,
                booked_for=booked_for or None,
                additional_support=additional_support or "",
            )
            created_count += 1

        if created_count > 0:
            messages.success(request, f"{created_count} booking(s) created successfully!")
        else:
            messages.warning(request, "No bookings were created due to errors or clashes.")

        return redirect('book_room', room_id=room.id)

    return render(request, "book_room.html", {
        "room": room,
        "bookings": bookings,
        "organizations": ORGANIZATIONS,
    })


@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this booking.")

    room_id = booking.room.id
    booking.delete()
    messages.success(request, "Booking deleted successfully.")
    return redirect('book_room', room_id=room_id)


@login_required
def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.user != booking.user and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to edit this booking.")

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save(commit=False)

            if updated_booking.start_time < dt_time(9, 0) or updated_booking.end_time > dt_time(22, 0):
                messages.error(request, "Booking must be between 9:00 and 22:00.")
            elif updated_booking.start_time >= updated_booking.end_time:
                messages.error(request, "End time must be after start time.")
            else:
                conflict = Booking.objects.filter(
                    room=updated_booking.room,
                    conference_date=updated_booking.conference_date
                ).exclude(id=updated_booking.id).filter(
                    start_time__lt=updated_booking.end_time,
                    end_time__gt=updated_booking.start_time
                )
                if conflict.exists():
                    messages.error(request, "This time slot is already booked.")
                else:
                    updated_booking.save()
                    messages.success(request, "Booking updated successfully.")
                    return redirect('book_room', room_id=updated_booking.room.id)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = BookingForm(instance=booking)

    return render(request, 'edit_booking.html', {
        'form': form,
        'booking': booking
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Logged in successfully.")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


@login_required
@require_GET
def filter_archived_bookings(request, room_id):
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)


    from_date = request.GET.get("from")
    to_date = request.GET.get("to")

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
        to_date = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    qs = ArchivedBooking.objects.filter(room_id=room_id)
    if from_date:
        qs = qs.filter(conference_date__gte=from_date)
    if to_date:
        qs = qs.filter(conference_date__lte=to_date)

    data = [
        {
            "title": b.title,
            "user": b.user.get_full_name() or b.user.username,
            "date": b.conference_date.strftime("%Y-%m-%d"),
            "start": b.start_time.strftime("%H:%M"),
            "end": b.end_time.strftime("%H:%M"),
            "organization": b.organization or "-",
            "booked_for": b.booked_for or "-",
            "notes": b.additional_support or "",
        }
        for b in qs.order_by("-conference_date")
    ]
    return JsonResponse({"bookings": data})


def archive_expired_bookings():
    today = localdate()
    expired_bookings = Booking.objects.filter(conference_date__lt=today)

    for booking in expired_bookings:
        ArchivedBooking.objects.create(
            original_booking_id=booking.id,
            user=booking.user,
            room=booking.room,
            title=booking.title,
            conference_date=booking.conference_date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            organization=booking.organization,
            booked_for=booking.booked_for,
            additional_support=booking.additional_support,
        )
        booking.delete()


