from rest_framework import serializers

from .models import Booking, Feedback, Hotel, HotelImage, Room, RoomImage



class RoomImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = RoomImage
        fields = ['id', 'room', 'image', 'image_url', 'alt_text', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {'room': {'required': False}}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class HotelImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HotelImage
        fields = ['id', 'hotel', 'image', 'image_url', 'alt_text', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {'hotel': {'required': False}}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url



class HotelSerializer(serializers.ModelSerializer):
    images = HotelImageSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'address', 'city', 'description', 'owner_name', 'owner_email', 'is_active', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    hotel_images = HotelImageSerializer(source='hotel.images', many=True, read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    hotel_details = HotelSerializer(source='hotel', read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'hotel', 'hotel_details', 'hotel_name', 'room_type', 'description', 'price_per_night', 'amenities', 'is_available', 'images', 'hotel_images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



class BookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.hotel.name', read_only=True)
    room_details = RoomSerializer(source='room', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'room', 'room_details', 'room_name', 'guest_name', 'guest_email', 'check_in', 'check_out', 'guests', 'total_price', 'status', 'is_paid', 'payment_method', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


    def validate(self, attrs):
        if attrs['check_out'] <= attrs['check_in']:
            raise serializers.ValidationError('Check-out must be after check-in.')

        room = attrs['room']
        if not room.is_available:
            raise serializers.ValidationError('This room is not available.')

        overlap = Booking.objects.filter(
            room=room,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
            check_in__lt=attrs['check_out'],
            check_out__gt=attrs['check_in'],
        ).exists()
        if overlap:
            raise serializers.ValidationError('This room is already booked for those dates.')
        return attrs

    def create(self, validated_data):
        nights = (validated_data['check_out'] - validated_data['check_in']).days
        validated_data['total_price'] = nights * validated_data['room'].price_per_night
        return super().create(validated_data)


class FeedbackSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)

    class Meta:
        model = Feedback
        fields = ['id', 'hotel', 'hotel_name', 'room', 'user_name', 'user_email', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

