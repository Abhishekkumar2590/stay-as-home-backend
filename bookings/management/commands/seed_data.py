import os

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bookings.models import Hotel, Room, Feedback

class Command(BaseCommand):
    help = 'Seeds initial sample hotels, rooms, and metrics for QuickStay'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding sample hotel data and superuser...')

        # 1. Check if superuser exists; create only if none exists and password is provided
        if not User.objects.filter(is_superuser=True).exists():
            admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
            admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD') or os.getenv('ADMIN_PASSWORD')
            admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@quickstay.com')
            if admin_password:
                User.objects.create_superuser(username=admin_username, email=admin_email, password=admin_password)
                self.stdout.write(self.style.SUCCESS(f'Created initial superuser: {admin_username}'))

        # 2. Seed Hotels and Rooms
        hotels_data = [
            {
                'name': 'The Azure Coastline Hotel',
                'address': '45 Ocean Drive',
                'city': 'Miami',
                'description': 'Luxury oceanfront resort with pristine beach access and panoramic Atlantic ocean views.',
                'owner_name': 'Abhishek Kumar',
                'owner_email': 'owner@quickstay.com',
                'is_active': True,
                'rooms': [
                    {'room_type': 'Presidential Suite', 'price_per_night': 399.00, 'amenities': 'Ocean View, King Bed, Jacuzzi, Free Breakfast, High-Speed WiFi, Mini Bar, Room Service'},
                    {'room_type': 'Deluxe Ocean View', 'price_per_night': 249.00, 'amenities': 'Balcony, King Bed, Free WiFi, Air Conditioning, Smart TV'},
                ]
            },
            {
                'name': 'Grand Highland Mountain Resort',
                'address': '12 Alpine Way',
                'city': 'Aspen',
                'description': 'Ski-in luxury mountain lodge surrounded by pine forests and scenic alpine vistas.',
                'owner_name': 'Abhishek Kumar',
                'owner_email': 'owner@quickstay.com',
                'is_active': True,
                'rooms': [
                    {'room_type': 'Mountain View Chalet', 'price_per_night': 320.00, 'amenities': 'Fireplace, Balcony, Mountain View, Heated Floors, Free Breakfast'},
                    {'room_type': 'Superior Double Room', 'price_per_night': 199.00, 'amenities': 'Queen Bed, Free WiFi, Mountain View, Coffee Maker'},
                ]
            },
            {
                'name': 'Metropolitan Urban Boutique Hotel',
                'address': '742 Broadway Avenue',
                'city': 'New York',
                'description': 'Chic modern boutique hotel located in the heart of downtown with rooftop lounge.',
                'owner_name': 'Abhishek Kumar',
                'owner_email': 'owner@quickstay.com',
                'is_active': True,
                'rooms': [
                    {'room_type': 'Executive Loft', 'price_per_night': 289.00, 'amenities': 'City Skyline View, King Bed, Workspace, Smart TV, Gym Access'},
                    {'room_type': 'Standard Urban Room', 'price_per_night': 159.00, 'amenities': 'Queen Bed, High-Speed WiFi, Coffee Bar, Luxury Toiletries'},
                ]
            },
            {
                'name': 'Serene Palms Sanctuary & Spa',
                'address': '88 Palm Grove Boulevard',
                'city': 'Goa',
                'description': 'Tropical wellness resort featuring world-class spa treatments and private infinity pools.',
                'owner_name': 'Abhishek Kumar',
                'owner_email': 'owner@quickstay.com',
                'is_active': True,
                'rooms': [
                    {'room_type': 'Private Pool Villa', 'price_per_night': 450.00, 'amenities': 'Private Pool, Garden View, King Bed, All-Inclusive Dining, Spa Voucher'},
                    {'room_type': 'Luxury Garden Suite', 'price_per_night': 210.00, 'amenities': 'Garden View, King Bed, Bathtub, Free Breakfast, Balcony'},
                ]
            }
        ]

        for h_data in hotels_data:
            rooms_info = h_data.pop('rooms')
            hotel, h_created = Hotel.objects.get_or_create(name=h_data['name'], defaults=h_data)
            if h_created:
                self.stdout.write(f'Created Hotel: {hotel.name}')
            else:
                self.stdout.write(f'Hotel already exists: {hotel.name}')

            for r_data in rooms_info:
                room, r_created = Room.objects.get_or_create(
                    hotel=hotel,
                    room_type=r_data['room_type'],
                    defaults={
                        'price_per_night': r_data['price_per_night'],
                        'amenities': r_data['amenities'],
                        'is_available': True,
                        'description': f'Spacious {r_data["room_type"]} at {hotel.name} with premium comforts.',
                    }
                )
                if r_created:
                    self.stdout.write(f'  - Created Room: {room.room_type} ($ {room.price_per_night}/night)')

        # Seed sample feedbacks
        if Feedback.objects.count() == 0:
            sample_hotel = Hotel.objects.first()
            sample_room = Room.objects.first()
            Feedback.objects.create(hotel=sample_hotel, room=sample_room, user_name='Sophia Martinez', user_email='sophia@example.com', rating=5, comment='Outstanding stay! The ocean views and room service exceeded all expectations.')
            Feedback.objects.create(hotel=sample_hotel, room=sample_room, user_name='David Chen', user_email='david@example.com', rating=5, comment='Clean, modern, and very comfortable. The staff went above and beyond.')
            Feedback.objects.create(hotel=sample_hotel, room=sample_room, user_name='Elena Rostova', user_email='elena@example.com', rating=4, comment='Beautiful architecture and great location. Will definitely return!')
            self.stdout.write('Created sample reviews and ratings.')

        self.stdout.write(self.style.SUCCESS('Successfully seeded QuickStay database!'))
