from django.db import models
from django.contrib.auth.models import User
from datetime import date, time


class Room(models.Model):
    name = models.CharField(max_length=100, default="Unnamed Room")
    capacity = models.PositiveIntegerField(default=10)

    def __str__(self):
        return self.name


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="Untitled Conference")
    conference_date = models.DateField(default=date.today)
    start_time = models.TimeField(default=time(9, 0))   # default 9:00 AM
    end_time = models.TimeField(default=time(10, 0))   # default 10:00 AM

    organization = models.CharField(max_length=100, blank=True, null=True, default="Not specified")  # allow empty
    booked_for = models.CharField(max_length=150, blank=True, null=True, default="Self")  # allow empty

    additional_support = models.TextField(
        blank=True,
        default="No additional support needed"
    )

    def __str__(self):
        user_display = self.user.username if self.user else "Unknown User"
        return f"{self.title} by {user_display} on {self.conference_date} ({self.room.name})"

    class Meta:
        ordering = ['conference_date', 'start_time']
        verbose_name = "Room Booking"
        verbose_name_plural = "Room Bookings"


class ArchivedBooking(models.Model):
    original_booking_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    conference_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    # ✅ also keep organization/booked_for in archive
    organization = models.CharField(max_length=100, blank=True, null=True, default="Not specified")  # ✅
    booked_for = models.CharField(max_length=150, blank=True, null=True, default="Self") 

    additional_support = models.TextField(blank=True, default="No additional support needed")
    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_display = self.user.username if self.user else "Unknown User"
        return f"Archived: {self.title} by {user_display} ({self.conference_date})"
