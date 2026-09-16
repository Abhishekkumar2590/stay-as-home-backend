from django.contrib.auth import views as auth_views
from django.urls import path

from . import management_views

urlpatterns = [
    path('login/', management_views.management_login, name='management-login'),
    path('logout/', management_views.management_logout, name='management-logout'),
    path('password-change/', management_views.management_password_change, name='management-password-change'),
    path('', management_views.dashboard, name='management-dashboard'),
    path('hotels/new/', management_views.hotel_create, name='hotel-create'),
    path('hotels/<int:hotel_id>/photos/', management_views.hotel_photos, name='hotel-photos'),
    path('rooms/new/', management_views.room_create, name='room-create'),
    path('rooms/<int:room_id>/photos/', management_views.room_photos, name='room-photos'),
    path('bookings/', management_views.booking_list, name='booking-list'),
    path('bookings/<int:booking_id>/cancel/', management_views.cancel_booking, name='booking-cancel'),
]
