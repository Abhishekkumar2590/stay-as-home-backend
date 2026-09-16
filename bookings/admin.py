from django.conf import settings
from django.contrib import admin

from .models import Booking, Feedback, Hotel, HotelImage, Room, RoomImage

admin.site.site_header = 'QuickStay Hotel Administration'
admin.site.site_title = 'QuickStay Admin'
admin.site.index_title = 'Hotel & Booking Management'
admin.site.site_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173/')


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ['image', 'alt_text']


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ['image', 'alt_text']


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'owner_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'city', 'owner_name']
    inlines = [HotelImageInline]


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'image', 'uploaded_at']
    search_fields = ['hotel__name', 'hotel__city']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'room_type', 'price_per_night', 'is_available', 'created_at']
    list_filter = ['room_type', 'is_available', 'hotel']
    search_fields = ['hotel__name', 'description']
    inlines = [RoomImageInline]


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room', 'image', 'uploaded_at']
    search_fields = ['room__hotel__name', 'room__room_type']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'guest_email', 'room', 'check_in', 'check_out', 'status', 'is_paid', 'payment_method', 'total_price']
    list_filter = ['status', 'is_paid', 'check_in', 'check_out']
    search_fields = ['guest_name', 'guest_email', 'room__hotel__name']
    readonly_fields = ['total_price', 'created_at']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'user_email', 'hotel', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user_name', 'user_email', 'comment']

