from django import forms

from .models import Hotel, HotelImage, Room, RoomImage


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ['name', 'address', 'city', 'description', 'owner_name', 'owner_email', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['hotel', 'room_type', 'description', 'price_per_night', 'amenities', 'is_available']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'amenities': forms.Textarea(attrs={'rows': 3, 'placeholder': '["Free WiFi", "Pool Access"]'})}


class RoomImageForm(forms.ModelForm):
    class Meta:
        model = RoomImage
        fields = ['image', 'alt_text']


class HotelImageForm(forms.ModelForm):
    class Meta:
        model = HotelImage
        fields = ['image', 'alt_text']
