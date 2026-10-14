
from datetime import datetime, date, time as dt_time, timedelta
import calendar
import hmac
import os
import random

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate, localtime, make_aware
from django.views.decorators.http import require_GET

from calendar import monthrange, month_name

from .forms import BookingForm, CustomLoginForm
from .models import Room, Booking, ArchivedBooking


# ============================================================
# CONSTANTS
# ============================================================

ORGANIZATIONS = [
    "SPSB",
    "BdMSO",
    "BdOSN",
    "WROBd",
    "IROC",
    "Malala Project",
    "BdMO",
    "Other",
]

BOOKING_COLORS = [
    "#fd7e14",
    "#6442ff",
    "#0dcaf0",
    "#dc3545",
    "#0d6efd",
    "#56EA00",
    "#C300FF",
]


# ============================================================
# ARCHIVE EXPIRED BOOKINGS
# ============================================================

def archive_expired_bookings():
    """
    Move all expired bookings from Booking to ArchivedBooking.

    A booking is considered expired when its actual end
    date/time has passed.

    This function is safe to call multiple times.
    """

    now = localtime()
    current_date = now.date()
    current_time = now.time()

    archived_count = 0

    with transaction.atomic():

        # Get bookings that are either:
        #
        # 1. From a previous date
        # OR
        #
        # 2. From today but their end time has passed
        #
        expired_bookings = (
            Booking.objects
            .select_for_update(of=("self",))
            .select_related("user", "room")
            .filter(
                conference_date__lte=current_date
            )
        )

        for booking in expired_bookings:

            # ------------------------------------------------
            # Determine whether the booking has actually ended
            # ------------------------------------------------

            if booking.conference_date < current_date:

                is_expired = True

            elif booking.conference_date == current_date:

                is_expired = booking.end_time <= current_time

            else:

                is_expired = False

            if not is_expired:
                continue

            # ------------------------------------------------
            # Prevent duplicate archive records
            # ------------------------------------------------

            already_archived = ArchivedBooking.objects.filter(
                original_booking_id=booking.id
            ).exists()

            if already_archived:
                booking.delete()
                continue

            # ------------------------------------------------
            # Copy booking into archive
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Remove active booking
            # ------------------------------------------------

            booking.delete()

            archived_count += 1

    return archived_count


# ============================================================
# HOME / CALENDAR
# ============================================================

def home(request):

    # --------------------------------------------------------
    # Archive expired bookings every time the calendar loads.
    #
    # Vercel Cron is still used as a backup, but the calendar
    # itself will never intentionally show expired bookings.
    # --------------------------------------------------------

    archive_expired_bookings()

    rooms = Room.objects.all()

    today = localdate()

    month = int(
        request.GET.get(
            "month",
            today.month
        )
    )

    year = int(
        request.GET.get(
            "year",
            today.year
        )
    )

    prev_month = (
        month - 1
        if month > 1
        else 12
    )

    prev_year = (
        year
        if month > 1
        else year - 1
    )

    next_month = (
        month + 1
        if month < 12
        else 1
    )

    next_year = (
        year
        if month < 12
        else year + 1
    )

    start_date = date(
        year,
        month,
        1
    )

    end_date = date(
        year,
        month,
        monthrange(year, month)[1]
    )

    bookings = list(
        Booking.objects
        .filter(
            conference_date__range=(
                start_date,
                end_date
            )
        )
        .select_related("user", "room")
        .order_by(
            "conference_date",
            "start_time"
        )
    )

    # --------------------------------------------------------
    # Group bookings by day
    # --------------------------------------------------------

    bookings_by_day = {}

    for booking in bookings:

        day = booking.conference_date.day

        if day not in bookings_by_day:
            bookings_by_day[day] = []

        bookings_by_day[day].append(booking)

    # --------------------------------------------------------
    # Assign random colors
    # --------------------------------------------------------

    for day, day_bookings in bookings_by_day.items():

        random.shuffle(day_bookings)

        for index, booking in enumerate(day_bookings):

            booking.color = (
                BOOKING_COLORS[
                    index % len(BOOKING_COLORS)
                ]
            )

    months = [
        (i, month_name[i])
        for i in range(1, 13)
    ]

    context = {
        "rooms": rooms,
        "bookings": bookings,
        "bookings_by_day": bookings_by_day,

        "selected_month": month,
        "selected_year": year,

        "prev_month": prev_month,
        "prev_year": prev_year,

        "next_month": next_month,
        "next_year": next_year,

        "months": months,

        "years": range(
            today.year,
            today.year + 3
        ),

        "month_year": (
            month,
            year
        ),
    }

    return render(
        request,
        "home.html",
        context
    )


# ============================================================
# BOOK ROOM
# ============================================================

@login_required
def book_room(request, room_id):

    # Make sure expired bookings are archived before
    # displaying the booking room.

    archive_expired_bookings()

    room = get_object_or_404(
        Room,
        id=room_id
    )

    bookings = (
        Booking.objects
        .filter(room=room)
        .select_related("user", "room")
        .order_by(
            "conference_date",
            "start_time"
        )
    )

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        additional_support = request.POST.get(
            "additional_support",
            ""
        ).strip()

        organization = request.POST.get(
            "organization",
            ""
        ).strip()

        booked_for = request.POST.get(
            "booked_for",
            ""
        ).strip()

        dates = request.POST.getlist(
            "conference_date[]"
        )

        start_times = request.POST.getlist(
            "start_time[]"
        )

        end_times = request.POST.getlist(
            "end_time[]"
        )

        if not dates or not start_times or not end_times:

            messages.error(
                request,
                "Please provide at least one booking slot."
            )

            return redirect(
                "book_room",
                room_id=room.id
            )

        created_count = 0

        for idx, (d, s, e) in enumerate(
            zip(
                dates,
                start_times,
                end_times
            ),
            start=1
        ):

            if not (d and s and e):

                messages.warning(
                    request,
                    f"Skipping empty slot #{idx}."
                )

                continue

            try:

                booking_date = datetime.strptime(
                    d,
                    "%Y-%m-%d"
                ).date()

                start = datetime.strptime(
                    s,
                    "%H:%M"
                ).time()

                end = datetime.strptime(
                    e,
                    "%H:%M"
                ).time()

            except ValueError:

                messages.error(
                    request,
                    f"Invalid date/time format in slot #{idx}."
                )

                continue

            # ------------------------------------------------
            # Validate time
            # ------------------------------------------------

            if start >= end:

                messages.error(
                    request,
                    f"Invalid time range on {booking_date} "
                    f"(slot #{idx})."
                )

                continue

            if (
                start < dt_time(9, 0)
                or end > dt_time(22, 0)
            ):

                messages.error(
                    request,
                    f"Booking on {booking_date} must be "
                    f"between 09:00 and 22:00."
                )

                continue

            # ------------------------------------------------
            # Prevent past dates
            # ------------------------------------------------

            if booking_date < localdate():

                messages.error(
                    request,
                    f"Invalid date {booking_date} "
                    f"(slot #{idx}): cannot book past dates."
                )

                continue

            # ------------------------------------------------
            # Check booking conflict
            # ------------------------------------------------

            if has_booking_conflict(
                room,
                booking_date,
                start,
                end
            ):

                available_time = (
                    datetime.combine(
                        booking_date,
                        end
                    )
                    + timedelta(hours=1)
                )

                messages.error(
                    request,
                    f"Bookings must have a 1-hour gap. "
                    f"Please choose a slot starting at or after "
                    f"{available_time:%H:%M} on {booking_date}."
                )

                continue

            # ------------------------------------------------
            # Create booking
            # ------------------------------------------------

            Booking.objects.create(
                user=request.user,
                room=room,
                title=(
                    title
                    or "Untitled Conference"
                ),
                conference_date=booking_date,
                start_time=start,
                end_time=end,
                organization=(
                    organization
                    or None
                ),
                booked_for=(
                    booked_for
                    or None
                ),
                additional_support=(
                    additional_support
                    or ""
                ),
            )

            created_count += 1

        if created_count > 0:

            messages.success(
                request,
                f"{created_count} booking(s) created successfully!"
            )

        else:

            messages.warning(
                request,
                "No bookings were created due to "
                "errors or clashes."
            )

        return redirect(
            "book_room",
            room_id=room.id
        )

    return render(
        request,
        "book_room.html",
        {
            "room": room,
            "bookings": bookings,
            "organizations": ORGANIZATIONS,
        }
    )


# ============================================================
# BOOKING CONFLICT
# ============================================================

def has_booking_conflict(
    room,
    booking_date,
    start_time,
    end_time,
    exclude_id=None
):

    existing_bookings = (
        Booking.objects
        .filter(
            room=room,
            conference_date=booking_date
        )
    )

    if exclude_id:

        existing_bookings = (
            existing_bookings
            .exclude(id=exclude_id)
        )

    proposed_start = datetime.combine(
        booking_date,
        start_time
    )

    proposed_end = datetime.combine(
        booking_date,
        end_time
    )

    min_gap = timedelta(
        hours=1
    )

    for booking in existing_bookings:

        existing_start = datetime.combine(
            booking_date,
            booking.start_time
        )

        existing_end = datetime.combine(
            booking_date,
            booking.end_time
        )

        if (
            proposed_start
            < existing_end + min_gap

            and

            proposed_end
            > existing_start - min_gap
        ):

            return True

    return False


# ============================================================
# DELETE BOOKING
# ============================================================

@login_required
def delete_booking(
    request,
    booking_id
):

    booking = get_object_or_404(
        Booking,
        pk=booking_id
    )

    if (
        request.user != booking.user
        and not request.user.is_superuser
    ):

        return HttpResponseForbidden(
            "You do not have permission "
            "to delete this booking."
        )

    room_id = booking.room.id

    booking.delete()

    messages.success(
        request,
        "Booking deleted successfully."
    )

    return redirect(
        "book_room",
        room_id=room_id
    )


# ============================================================
# EDIT BOOKING
# ============================================================

@login_required
def edit_booking(
    request,
    booking_id
):

    booking = get_object_or_404(
        Booking,
        pk=booking_id
    )

    if (
        request.user != booking.user
        and not request.user.is_superuser
    ):

        return HttpResponseForbidden(
            "You do not have permission "
            "to edit this booking."
        )

    if request.method == "POST":

        form = BookingForm(
            request.POST,
            instance=booking
        )

        if form.is_valid():

            updated_booking = form.save(
                commit=False
            )

            if (
                updated_booking.start_time
                < dt_time(9, 0)

                or

                updated_booking.end_time
                > dt_time(22, 0)
            ):

                messages.error(
                    request,
                    "Booking must be between 9:00 and 22:00."
                )

            elif (
                updated_booking.start_time
                >= updated_booking.end_time
            ):

                messages.error(
                    request,
                    "End time must be after start time."
                )

            else:

                if has_booking_conflict(
                    updated_booking.room,
                    updated_booking.conference_date,
                    updated_booking.start_time,
                    updated_booking.end_time,
                    exclude_id=updated_booking.id,
                ):

                    messages.error(
                        request,
                        "This booking conflicts with an existing "
                        "slot or violates the required 1-hour gap."
                    )

                else:

                    updated_booking.save()

                    messages.success(
                        request,
                        "Booking updated successfully."
                    )

                    return redirect(
                        "book_room",
                        room_id=updated_booking.room.id
                    )

        else:

            messages.error(
                request,
                "Please correct the errors in the form."
            )

    else:

        form = BookingForm(
            instance=booking
        )

    return render(
        request,
        "edit_booking.html",
        {
            "form": form,
            "booking": booking
        }
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:

        return redirect(
            "home"
        )

    if request.method == "POST":

        form = CustomLoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            login(
                request,
                form.get_user()
            )

            messages.success(
                request,
                "Logged in successfully."
            )

            return redirect(
                "home"
            )

        messages.error(
            request,
            "Invalid username or password."
        )

    else:

        form = CustomLoginForm()

    return render(
        request,
        "login.html",
        {
            "form": form
        }
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        "Logged out successfully."
    )

    return redirect(
        "login"
    )


# ============================================================
# ARCHIVED BOOKINGS FILTER
# ============================================================

@login_required
@require_GET
def filter_archived_bookings(
    request,
    room_id
):

    if not request.user.is_staff:

        return JsonResponse(
            {
                "error": "Unauthorized"
            },
            status=403
        )

    from_date = request.GET.get(
        "from"
    )

    to_date = request.GET.get(
        "to"
    )

    try:

        from_date = (
            datetime.strptime(
                from_date,
                "%Y-%m-%d"
            ).date()
            if from_date
            else None
        )

        to_date = (
            datetime.strptime(
                to_date,
                "%Y-%m-%d"
            ).date()
            if to_date
            else None
        )

    except ValueError:

        return JsonResponse(
            {
                "error": "Invalid date format"
            },
            status=400
        )

    bookings = (
        ArchivedBooking.objects
        .filter(room_id=room_id)
        .select_related("user", "room")
    )

    if from_date:

        bookings = bookings.filter(
            conference_date__gte=from_date
        )

    if to_date:

        bookings = bookings.filter(
            conference_date__lte=to_date
        )

    data = []

    for booking in bookings.order_by(
        "-conference_date",
        "-start_time"
    ):

        data.append({

            "title": booking.title,

            "user": (
                booking.user.get_full_name()
                or booking.user.username
            )
            if booking.user
            else "Unknown user",

            "date": (
                booking.conference_date.strftime(
                    "%Y-%m-%d"
                )
            ),

            "start": (
                booking.start_time.strftime(
                    "%H:%M"
                )
            ),

            "end": (
                booking.end_time.strftime(
                    "%H:%M"
                )
            ),

            "organization": (
                booking.organization
                or "-"
            ),

            "booked_for": (
                booking.booked_for
                or "-"
            ),

            "notes": (
                booking.additional_support
                or ""
            ),
        })

    return JsonResponse(
        {
            "bookings": data
        }
    )


# ============================================================
# VERCEL CRON ENDPOINT
# ============================================================

@require_GET
def archive_expired_bookings_cron(request):

    secret = os.environ.get(
        "CRON_SECRET"
    )

    if not secret:

        return JsonResponse(
            {
                "error":
                    "CRON_SECRET is not configured"
            },
            status=503
        )

    authorization = request.headers.get(
        "Authorization",
        ""
    )

    expected_authorization = (
        f"Bearer {secret}"
    )

    if not hmac.compare_digest(
        authorization,
        expected_authorization
    ):

        return JsonResponse(
            {
                "error": "Unauthorized"
            },
            status=403
        )

    archived_count = (
        archive_expired_bookings()
    )

    return JsonResponse(
        {
            "success": True,
            "archived": archived_count,
            "message": (
                f"{archived_count} expired "
                f"booking(s) archived successfully."
            )
        }
    )
