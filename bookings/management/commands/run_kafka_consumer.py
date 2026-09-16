import json
import logging
import signal
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from bookings.kafka_service import (
    ALL_TOPICS,
    EVENT_BOOKING_CANCELLED,
    EVENT_BOOKING_CONFIRMED,
    EVENT_BOOKING_CREATED,
    EVENT_FEEDBACK_SUBMITTED,
    EVENT_PAYMENT_SUCCESS,
    EVENT_ROOM_CREATED,
    EVENT_ROOM_UPDATED,
)
from bookings.cache_service import invalidate_room_caches

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs the Apache Kafka background event consumer for QuickStay Hotel Service.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topics',
            nargs='+',
            default=ALL_TOPICS,
            help='List of Kafka topics to subscribe to (defaults to all hotel topics)',
        )
        parser.add_argument(
            '--group-id',
            default=getattr(settings, 'KAFKA_CONSUMER_GROUP', 'quickstay-consumer-group'),
            help='Kafka consumer group identifier',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test configuration and exit without long-running polling loop',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Poll once for available messages and exit',
        )

    def handle(self, *args, **options):
        topics = options['topics']
        group_id = options['group_id']
        dry_run = options['dry_run']
        once = options['once']
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:9092').split(',')

        self.stdout.write(self.style.SUCCESS(f"=== QuickStay Kafka Event Consumer ==="))
        self.stdout.write(f"Bootstrap Servers: {bootstrap_servers}")
        self.stdout.write(f"Consumer Group:   {group_id}")
        self.stdout.write(f"Subscribed Topics: {', '.join(topics)}")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("[Dry Run] Consumer configuration verified successfully."))
            return

        try:
            from kafka import KafkaConsumer
        except ImportError:
            self.stderr.write(self.style.ERROR("kafka-python-ng is not installed."))
            return

        running = True

        def shutdown_handler(signum, frame):
            nonlocal running
            self.stdout.write("\nGracefully shutting down Kafka consumer worker...")
            running = False

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000,
            )
            self.stdout.write(self.style.SUCCESS(f"Connected to Kafka broker. Listening for live event stream... (Press Ctrl+C to stop)\n"))
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"Could not connect to Kafka broker at {bootstrap_servers}: {e}"))
            self.stderr.write("Make sure Apache Kafka is running on port 9092.")
            return

        processed_count = 0
        while running:
            try:
                for message in consumer:
                    if not running:
                        break

                    topic = message.topic
                    payload = message.value
                    event_type = payload.get('event_type', 'UNKNOWN')
                    event_id = payload.get('event_id', 'N/A')
                    data = payload.get('payload', {})

                    self.process_event(topic, event_type, event_id, data)
                    processed_count += 1

                    if once:
                        running = False
                        break
            except Exception as loop_err:
                if running:
                    logger.debug(f"Consumer poll idle or error: {loop_err}")
                    time.sleep(0.5)

        consumer.close()
        self.stdout.write(self.style.SUCCESS(f"Kafka consumer stopped. Total messages processed: {processed_count}"))

    def process_event(self, topic, event_type, event_id, data):
        """Process incoming Kafka domain events."""
        self.stdout.write(f"[{time.strftime('%X')}] Received event [{event_type}] on topic [{topic}] | ID: {event_id}")

        if event_type == EVENT_BOOKING_CREATED:
            guest_name = data.get('guest_name', 'Guest')
            hotel_name = data.get('hotel_name', 'Hotel')
            total_price = data.get('total_price', 0)
            self.stdout.write(self.style.SUCCESS(f"  -> Booking Created: {guest_name} at {hotel_name} (${total_price})"))
            invalidate_room_caches()

        elif event_type == EVENT_BOOKING_CONFIRMED or event_type == EVENT_PAYMENT_SUCCESS:
            booking_id = data.get('booking_id')
            self.stdout.write(self.style.SUCCESS(f"  -> Payment/Booking Confirmed for booking ID #{booking_id}. Receipt triggered."))
            invalidate_room_caches()

        elif event_type == EVENT_BOOKING_CANCELLED:
            booking_id = data.get('booking_id')
            self.stdout.write(self.style.WARNING(f"  -> Booking Cancelled: ID #{booking_id}. Inventory released."))
            invalidate_room_caches()

        elif event_type in (EVENT_ROOM_CREATED, EVENT_ROOM_UPDATED):
            room_id = data.get('room_id')
            self.stdout.write(self.style.SUCCESS(f"  -> Room inventory updated: #{room_id}. Cache invalidated."))
            invalidate_room_caches()

        elif event_type == EVENT_FEEDBACK_SUBMITTED:
            user_name = data.get('user_name', 'Guest')
            rating = data.get('rating', 5)
            self.stdout.write(self.style.SUCCESS(f"  -> Guest review received from {user_name} ({rating}/5 stars)."))
