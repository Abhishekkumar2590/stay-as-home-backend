from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HotelForm, HotelImageForm, RoomForm, RoomImageForm
from .kafka_service import get_kafka_status
from .models import Booking, Hotel, HotelImage, Room, RoomImage


def management_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('management-dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                next_url = request.GET.get('next') or request.POST.get('next') or '/manage/'
                return redirect(next_url)
            else:
                error = 'This account does not have staff management privileges.'
        else:
            error = 'Invalid username or password. Please check your credentials.'

    return render(request, 'management/login.html', {'error': error})


@login_required(login_url='/manage/login/')
def management_password_change(request):
    if not request.user.is_staff:
        return render(request, 'management/forbidden.html', status=403)

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('management-dashboard')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'management/password_change.html', {'form': form})


def management_logout(request):
    auth_logout(request)
    return redirect(getattr(settings, 'FRONTEND_URL', '/'))


def staff_required(view):
    @wraps(view)
    @login_required(login_url='/manage/login/')
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return render(request, 'management/forbidden.html', status=403)
        return view(request, *args, **kwargs)
    return wrapped


@staff_required
def dashboard(request):
    kafka_status = get_kafka_status()
    context = {
        'hotel_count': Hotel.objects.count(),
        'room_count': Room.objects.count(),
        'booking_count': Booking.objects.count(),
        'recent_bookings': Booking.objects.select_related('room', 'room__hotel')[:8],
        'rooms': Room.objects.select_related('hotel').annotate(photo_count=Count('images'))[:8],
        'kafka_status': kafka_status,
    }
    return render(request, 'management/dashboard.html', context)


@staff_required
def hotel_create(request):
    form = HotelForm(request.POST or None)
    if form.is_valid():
        hotel = form.save()
        photos = []
        for image in request.FILES.getlist('images'):
            photo = HotelImage(hotel=hotel, image=image)
            photo.save()
            photos.append(photo)
        messages.success(request, f'Hotel created with {len(photos)} photo(s).')
        return redirect('management-dashboard')
    return render(request, 'management/form.html', {'form': form, 'title': 'Add hotel', 'button': 'Save hotel', 'image_label': 'Hotel photos'})


@staff_required
def room_create(request):
    form = RoomForm(request.POST or None)
    if form.is_valid():
        room = form.save()
        photos = []
        for image in request.FILES.getlist('images'):
            photo = RoomImage(room=room, image=image)
            photo.save()
            photos.append(photo)
        messages.success(request, f'Room created with {len(photos)} photo(s).')
        return redirect('management-dashboard')
    return render(request, 'management/form.html', {'form': form, 'title': 'Add room', 'button': 'Save room', 'image_label': 'Room photos'})


@staff_required
def room_photos(request, room_id):
    room = get_object_or_404(Room.objects.select_related('hotel').prefetch_related('images'), id=room_id)
    form = RoomImageForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        photo = form.save(commit=False)
        photo.room = room
        photo.save()
        messages.success(request, 'Room photo uploaded.')
        return redirect('room-photos', room_id=room.id)
    return render(request, 'management/photos.html', {'room': room, 'form': form})


@staff_required
def hotel_photos(request, hotel_id):
    hotel = get_object_or_404(Hotel.objects.prefetch_related('images'), id=hotel_id)
    form = HotelImageForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        photo = form.save(commit=False)
        photo.hotel = hotel
        photo.save()
        messages.success(request, 'Hotel photo uploaded.')
        return redirect('hotel-photos', hotel_id=hotel.id)
    return render(request, 'management/hotel_photos.html', {'hotel': hotel, 'form': form})


@staff_required
def booking_list(request):
    bookings = Booking.objects.select_related('room', 'room__hotel')
    page = Paginator(bookings, 15).get_page(request.GET.get('page'))
    return render(request, 'management/bookings.html', {'page': page})


@staff_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status'])
        messages.success(request, 'Booking cancelled.')
    return redirect('booking-list')
