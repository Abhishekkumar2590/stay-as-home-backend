from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AnalyticsSummaryView,
    BookingViewSet,
    CreateCashfreeOrderView,
    FeedbackViewSet,
    HotelImageViewSet,
    HotelViewSet,
    KafkaStatusView,
    KafkaTestPublishView,
    RoomImageViewSet,
    RoomViewSet,
    VerifyCashfreeOrderView,
)

router = DefaultRouter()
router.register('hotels', HotelViewSet)
router.register('rooms', RoomViewSet)
router.register('room-images', RoomImageViewSet)
router.register('hotel-images', HotelImageViewSet)
router.register('bookings', BookingViewSet)
router.register('feedbacks', FeedbackViewSet)

urlpatterns = [
    path('analytics/summary/', AnalyticsSummaryView.as_view(), name='analytics-summary'),
    path('kafka/status/', KafkaStatusView.as_view(), name='kafka-status'),
    path('kafka/publish-test/', KafkaTestPublishView.as_view(), name='kafka-publish-test'),
    path('payments/cashfree/create-order/', CreateCashfreeOrderView.as_view(), name='cashfree-create-order'),
    path('payments/cashfree/verify/', VerifyCashfreeOrderView.as_view(), name='cashfree-verify-order'),
] + router.urls


