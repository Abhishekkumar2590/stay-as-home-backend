from django.core.validators import MinValueValidator
from django.db import models


class Hotel(models.Model):
    name = models.CharField(max_length=160)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner_name = models.CharField(max_length=120, blank=True)
    owner_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.city}'


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotels/%Y/%m/')
    alt_text = models.CharField(max_length=160, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo for {self.hotel}'


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = 'single', 'Single Bed'
        DOUBLE = 'double', 'Double Bed'
        SUITE = 'suite', 'Suite'

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    description = models.TextField(blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amenities = models.JSONField(default=list, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.hotel.name} - {self.get_room_type_display()}'


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/%Y/%m/')
    alt_text = models.CharField(max_length=160, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Photo for {self.room}'


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmed'
        PENDING = 'pending', 'Pending'
        CANCELLED = 'cancelled', 'Cancelled'

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    guest_name = models.CharField(max_length=120)
    guest_email = models.EmailField()
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    is_paid = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=50, blank=True, default='Credit Card')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.guest_name} - {self.room}'


class Feedback(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    user_name = models.CharField(max_length=120)
    user_email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_name} - {self.rating}★'


