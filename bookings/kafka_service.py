import json
import logging
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from django.conf import settings

logger = logging.getLogger(__name__)

# Kafka Topics
TOPIC_BOOKINGS = 'hotel.bookings'
TOPIC_PAYMENTS = 'hotel.payments'
TOPIC_ROOMS = 'hotel.rooms'
TOPIC_FEEDBACKS = 'hotel.feedbacks'
TOPIC_NOTIFICATIONS = 'hotel.notifications'

ALL_TOPICS = [
    TOPIC_BOOKINGS,
    TOPIC_PAYMENTS,
    TOPIC_ROOMS,
    TOPIC_FEEDBACKS,
    TOPIC_NOTIFICATIONS,
]

# Event Types
EVENT_BOOKING_CREATED = 'BOOKING_CREATED'
EVENT_BOOKING_CONFIRMED = 'BOOKING_CONFIRMED'
EVENT_BOOKING_CANCELLED = 'BOOKING_CANCELLED'
EVENT_PAYMENT_INITIATED = 'PAYMENT_INITIATED'
EVENT_PAYMENT_SUCCESS = 'PAYMENT_SUCCESS'
EVENT_PAYMENT_FAILED = 'PAYMENT_FAILED'
EVENT_ROOM_CREATED = 'ROOM_CREATED'
EVENT_ROOM_UPDATED = 'ROOM_UPDATED'
EVENT_ROOM_DELETED = 'ROOM_DELETED'
EVENT_FEEDBACK_SUBMITTED = 'FEEDBACK_SUBMITTED'
EVENT_SYSTEM_TEST = 'SYSTEM_TEST_EVENT'

# In-memory rolling buffer for event stream monitoring (last 100 events)
_MAX_EVENT_BUFFER = 100
_EVENT_STREAM_LOCK = threading.Lock()
_EVENT_STREAM = deque(maxlen=_MAX_EVENT_BUFFER)
_EVENT_METRICS = {
    'total_published': 0,
    'total_failed': 0,
    'by_topic': {t: 0 for t in ALL_TOPICS},
    'by_event_type': {},
    'last_published_at': None,
}

_PRODUCER_INSTANCE = None
_PRODUCER_LOCK = threading.Lock()
_LAST_CONNECT_ATTEMPT = 0
_CONNECT_COOLDOWN_SECONDS = 10
_IS_BROKER_AVAILABLE = False


def _json_serializer(data):
    """Serialize event data dictionary to JSON bytes."""
    return json.dumps(data, default=str).encode('utf-8')


def get_kafka_producer():
    """
    Returns a thread-safe singleton KafkaProducer instance.
    If the Kafka broker is unreachable, returns None without raising errors.
    """
    global _PRODUCER_INSTANCE, _LAST_CONNECT_ATTEMPT, _IS_BROKER_AVAILABLE

    if not getattr(settings, 'KAFKA_ENABLED', True):
        return None

    if _PRODUCER_INSTANCE is not None:
        return _PRODUCER_INSTANCE

    now = time.time()
    if now - _LAST_CONNECT_ATTEMPT < _CONNECT_COOLDOWN_SECONDS:
        return None

    with _PRODUCER_LOCK:
        if _PRODUCER_INSTANCE is not None:
            return _PRODUCER_INSTANCE

        _LAST_CONNECT_ATTEMPT = now
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092')
        client_id = getattr(settings, 'KAFKA_CLIENT_ID', 'quickstay-hotel-service')

        try:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers.split(','),
                client_id=client_id,
                value_serializer=_json_serializer,
                key_serializer=lambda k: str(k).encode('utf-8') if k is not None else None,
                request_timeout_ms=3000,
                max_block_ms=2000,
                retries=2,
                acks='all',
            )
            _PRODUCER_INSTANCE = producer
            _IS_BROKER_AVAILABLE = True
            logger.info(f"Connected to Kafka broker at {bootstrap_servers}")
            return _PRODUCER_INSTANCE
        except Exception as e:
            _IS_BROKER_AVAILABLE = False
            logger.warning(f"Kafka broker not available at {bootstrap_servers} ({e}). Running in fallback event-buffer mode.")
            return None


def publish_event(topic, event_type, data, key=None):
    """
    Publishes an event to Kafka and records it in the live event stream monitor.
    Guaranteed non-blocking and fail-safe.
    """
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    envelope = {
        'event_id': event_id,
        'event_type': event_type,
        'topic': topic,
        'timestamp': timestamp,
        'source': getattr(settings, 'KAFKA_CLIENT_ID', 'quickstay-hotel-service'),
        'payload': data,
    }

    # Record in live in-memory event stream & update metrics
    with _EVENT_STREAM_LOCK:
        _EVENT_STREAM.appendleft(envelope)
        _EVENT_METRICS['total_published'] += 1
        _EVENT_METRICS['last_published_at'] = timestamp
        _EVENT_METRICS['by_topic'][topic] = _EVENT_METRICS['by_topic'].get(topic, 0) + 1
        _EVENT_METRICS['by_event_type'][event_type] = _EVENT_METRICS['by_event_type'].get(event_type, 0) + 1

    # Attempt publishing to real Kafka broker
    producer = get_kafka_producer()
    if producer:
        try:
            future = producer.send(topic, value=envelope, key=key)
            # Asynchronously send without blocking
            return {
                'status': 'published',
                'event_id': event_id,
                'topic': topic,
                'event_type': event_type,
                'broker_connected': True,
                'timestamp': timestamp,
            }
        except Exception as e:
            logger.warning(f"Failed to publish event to Kafka topic {topic}: {e}")
            with _EVENT_STREAM_LOCK:
                _EVENT_METRICS['total_failed'] += 1

    return {
        'status': 'buffered',
        'event_id': event_id,
        'topic': topic,
        'event_type': event_type,
        'broker_connected': False,
        'timestamp': timestamp,
        'note': 'Recorded in live in-memory event stream (Kafka broker offline/fallback mode)',
    }


def publish_booking_event(action, booking):
    """Publish booking events (CREATED, CONFIRMED, CANCELLED)."""
    if hasattr(booking, 'id'):
        booking_id = booking.id
        hotel_name = booking.room.hotel.name if booking.room and booking.room.hotel else 'Hotel'
        room_type = booking.room.room_type if booking.room else 'Room'
        guest_name = booking.guest_name
        guest_email = booking.guest_email
        check_in = str(booking.check_in)
        check_out = str(booking.check_out)
        total_price = float(booking.total_price)
        is_paid = booking.is_paid
        status = booking.status
    else:
        booking_id = booking.get('id')
        hotel_name = booking.get('hotel_name', 'Hotel')
        room_type = booking.get('room_type', 'Room')
        guest_name = booking.get('guest_name', 'Guest')
        guest_email = booking.get('guest_email', '')
        check_in = booking.get('check_in', '')
        check_out = booking.get('check_out', '')
        total_price = float(booking.get('total_price', 0))
        is_paid = booking.get('is_paid', False)
        status = booking.get('status', 'confirmed')

    event_type = (
        EVENT_BOOKING_CANCELLED if action == 'cancelled' or status == 'cancelled'
        else EVENT_BOOKING_CONFIRMED if is_paid
        else EVENT_BOOKING_CREATED
    )

    data = {
        'booking_id': booking_id,
        'action': action,
        'hotel_name': hotel_name,
        'room_type': room_type,
        'guest_name': guest_name,
        'guest_email': guest_email,
        'check_in': check_in,
        'check_out': check_out,
        'total_price': total_price,
        'is_paid': is_paid,
        'status': status,
    }

    return publish_event(
        topic=TOPIC_BOOKINGS,
        event_type=event_type,
        data=data,
        key=str(booking_id),
    )


def publish_payment_event(action, payment_data):
    """Publish payment events (INITIATED, SUCCESS, FAILED)."""
    event_type = (
        EVENT_PAYMENT_SUCCESS if action == 'success' or payment_data.get('is_paid')
        else EVENT_PAYMENT_FAILED if action == 'failed'
        else EVENT_PAYMENT_INITIATED
    )

    return publish_event(
        topic=TOPIC_PAYMENTS,
        event_type=event_type,
        data=payment_data,
        key=str(payment_data.get('booking_id') or payment_data.get('order_id') or 'payment'),
    )


def publish_room_event(action, room):
    """Publish room inventory events (CREATED, UPDATED, DELETED)."""
    if hasattr(room, 'id'):
        room_id = room.id
        hotel_id = room.hotel_id
        hotel_name = room.hotel.name if room.hotel else ''
        room_type = room.room_type
        price = float(room.price_per_night)
        is_available = room.is_available
    else:
        room_id = room.get('id')
        hotel_id = room.get('hotel')
        hotel_name = room.get('hotel_name', '')
        room_type = room.get('room_type', 'Single')
        price = float(room.get('price_per_night', 0))
        is_available = room.get('is_available', True)

    event_type = (
        EVENT_ROOM_CREATED if action == 'created'
        else EVENT_ROOM_DELETED if action == 'deleted'
        else EVENT_ROOM_UPDATED
    )

    data = {
        'room_id': room_id,
        'hotel_id': hotel_id,
        'hotel_name': hotel_name,
        'room_type': room_type,
        'price_per_night': price,
        'is_available': is_available,
        'action': action,
    }

    return publish_event(
        topic=TOPIC_ROOMS,
        event_type=event_type,
        data=data,
        key=str(room_id),
    )


def publish_feedback_event(action, feedback):
    """Publish guest feedback events."""
    if hasattr(feedback, 'id'):
        feedback_id = feedback.id
        hotel_name = feedback.hotel.name if feedback.hotel else 'General'
        user_name = feedback.user_name
        rating = feedback.rating
        comment = feedback.comment
    else:
        feedback_id = feedback.get('id')
        hotel_name = feedback.get('hotel_name', 'General')
        user_name = feedback.get('user_name', 'Guest')
        rating = feedback.get('rating', 5)
        comment = feedback.get('comment', '')

    data = {
        'feedback_id': feedback_id,
        'hotel_name': hotel_name,
        'user_name': user_name,
        'rating': rating,
        'comment': comment,
        'action': action,
    }

    return publish_event(
        topic=TOPIC_FEEDBACKS,
        event_type=EVENT_FEEDBACK_SUBMITTED,
        data=data,
        key=str(feedback_id),
    )


def get_kafka_status():
    """Returns real-time Kafka connectivity, topic metrics, and recent event stream."""
    producer = get_kafka_producer()
    bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092')
    enabled = getattr(settings, 'KAFKA_ENABLED', True)

    with _EVENT_STREAM_LOCK:
        events_list = list(_EVENT_STREAM)
        metrics = dict(_EVENT_METRICS)

    return {
        'enabled': enabled,
        'connected': _IS_BROKER_AVAILABLE,
        'mode': 'Live Kafka Broker' if _IS_BROKER_AVAILABLE else 'In-Memory Event Streaming Buffer',
        'bootstrap_servers': bootstrap_servers,
        'client_id': getattr(settings, 'KAFKA_CLIENT_ID', 'quickstay-hotel-service'),
        'consumer_group': getattr(settings, 'KAFKA_CONSUMER_GROUP', 'quickstay-consumer-group'),
        'topics': ALL_TOPICS,
        'metrics': metrics,
        'recent_events_count': len(events_list),
        'recent_events': events_list[:30],
    }


def clear_event_log():
    """Clears the live event buffer."""
    with _EVENT_STREAM_LOCK:
        _EVENT_STREAM.clear()
        _EVENT_METRICS['total_published'] = 0
        _EVENT_METRICS['total_failed'] = 0
        for k in _EVENT_METRICS['by_topic']:
            _EVENT_METRICS['by_topic'][k] = 0
        _EVENT_METRICS['by_event_type'].clear()
        _EVENT_METRICS['last_published_at'] = None
    return {'status': 'cleared', 'message': 'Kafka event stream log reset'}
