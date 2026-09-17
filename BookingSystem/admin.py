from django.contrib import admin
from .models import Room, Booking, ArchivedBooking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'get_user_name', 'conference_date', 'start_time', 'end_time')
    list_filter = ('room', 'conference_date')
    search_fields = ('title', 'room__name', 'user__username', 'user__first_name', 'user__last_name')
    ordering = ('-conference_date', 'start_time')

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return "Unknown"
    get_user_name.short_description = 'Booked By'
    
@admin.register(ArchivedBooking)
class ArchivedBookingAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'conference_date', 'start_time', 'end_time', 'archived_at')
    list_filter = ('room', 'conference_date', 'archived_at')
    search_fields = ('title', 'room__name')
    ordering = ('-archived_at',)