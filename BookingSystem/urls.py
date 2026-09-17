from django.urls import path 
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('booking/<int:booking_id>/delete/', views.delete_booking, name='delete_booking'),
    path('booking/<int:booking_id>/edit/', views.edit_booking, name='edit_booking'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path("rooms/<int:room_id>/archived/filter/", views.filter_archived_bookings, name="filter_archived_bookings"),
    path('rooms/<int:room_id>/archived/filter/', views.filter_archived_bookings, name='filter_archived'),


]

