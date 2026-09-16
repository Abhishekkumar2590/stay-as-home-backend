import logging
import threading
import time
from collections import defaultdict
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_ROOMS = 'rooms_list_all'
CACHE_KEY_HOTELS = 'hotels_list_all'
CACHE_KEY_ANALYTICS = 'analytics_summary_data'
CACHE_KEY_FEEDBACKS = 'feedbacks_list_all'

DEFAULT_CACHE_TTL = 600

_LOCAL_CACHE = {}
_ROOM_VIEWS = defaultdict(int)
_ONLINE_USERS = set()
_LOCKS = defaultdict(threading.Lock)
_RATE_LIMITS = defaultdict(list)
_SERVICE_LOCK = threading.Lock()


def get_cached_rooms():
    try:
        val = cache.get(CACHE_KEY_ROOMS)
        if val is not None:
            return val
    except Exception as e:
        logger.debug(f"Cache get rooms: {e}")
    return _LOCAL_CACHE.get(CACHE_KEY_ROOMS)


def set_cached_rooms(rooms_data, timeout=DEFAULT_CACHE_TTL):
    try:
        cache.set(CACHE_KEY_ROOMS, rooms_data, timeout=timeout)
    except Exception as e:
        logger.debug(f"Cache set rooms: {e}")
    _LOCAL_CACHE[CACHE_KEY_ROOMS] = rooms_data


def get_cached_hotels():
    try:
        val = cache.get(CACHE_KEY_HOTELS)
        if val is not None:
            return val
    except Exception as e:
        logger.debug(f"Cache get hotels: {e}")
    return _LOCAL_CACHE.get(CACHE_KEY_HOTELS)


def set_cached_hotels(hotels_data, timeout=DEFAULT_CACHE_TTL):
    try:
        cache.set(CACHE_KEY_HOTELS, hotels_data, timeout=timeout)
    except Exception as e:
        logger.debug(f"Cache set hotels: {e}")
    _LOCAL_CACHE[CACHE_KEY_HOTELS] = hotels_data


def get_cached_analytics():
    try:
        val = cache.get(CACHE_KEY_ANALYTICS)
        if val is not None:
            return val
    except Exception as e:
        logger.debug(f"Cache get analytics: {e}")
    return _LOCAL_CACHE.get(CACHE_KEY_ANALYTICS)


def set_cached_analytics(analytics_data, timeout=300):
    try:
        cache.set(CACHE_KEY_ANALYTICS, analytics_data, timeout=timeout)
    except Exception as e:
        logger.debug(f"Cache set analytics: {e}")
    _LOCAL_CACHE[CACHE_KEY_ANALYTICS] = analytics_data


def invalidate_room_caches():
    try:
        cache.delete(CACHE_KEY_ROOMS)
        cache.delete(CACHE_KEY_ANALYTICS)
    except Exception as e:
        logger.debug(f"Cache invalidate rooms: {e}")
    _LOCAL_CACHE.pop(CACHE_KEY_ROOMS, None)
    _LOCAL_CACHE.pop(CACHE_KEY_ANALYTICS, None)


def invalidate_hotel_caches():
    try:
        cache.delete(CACHE_KEY_HOTELS)
        cache.delete(CACHE_KEY_ROOMS)
        cache.delete(CACHE_KEY_ANALYTICS)
    except Exception as e:
        logger.debug(f"Cache invalidate hotels: {e}")
    _LOCAL_CACHE.pop(CACHE_KEY_HOTELS, None)
    _LOCAL_CACHE.pop(CACHE_KEY_ROOMS, None)
    _LOCAL_CACHE.pop(CACHE_KEY_ANALYTICS, None)


def invalidate_analytics_cache():
    try:
        cache.delete(CACHE_KEY_ANALYTICS)
    except Exception as e:
        logger.debug(f"Cache invalidate analytics: {e}")
    _LOCAL_CACHE.pop(CACHE_KEY_ANALYTICS, None)


def increment_room_view(room_id):
    with _SERVICE_LOCK:
        _ROOM_VIEWS[str(room_id)] += 1
        return _ROOM_VIEWS[str(room_id)]


def get_room_view(room_id):
    with _SERVICE_LOCK:
        return max(_ROOM_VIEWS.get(str(room_id), 1), 1)


def track_online_user(user_identifier):
    if user_identifier:
        with _SERVICE_LOCK:
            _ONLINE_USERS.add(str(user_identifier).lower().strip())


def get_online_users_count():
    with _SERVICE_LOCK:
        return max(len(_ONLINE_USERS), 4)


def acquire_room_lock(room_id, check_in, check_out, timeout=10):
    lock_key = f"room_lock_{room_id}_{check_in}_{check_out}"
    lock = _LOCKS[lock_key]
    return lock.acquire(blocking=True, timeout=timeout)


def release_room_lock(room_id, check_in, check_out):
    lock_key = f"room_lock_{room_id}_{check_in}_{check_out}"
    lock = _LOCKS.get(lock_key)
    if lock and lock.locked():
        try:
            lock.release()
        except RuntimeError:
            pass


def is_rate_limited(identifier, action='default', max_attempts=20, window_seconds=60):
    now = time.time()
    key = f"{action}:{identifier}"
    with _SERVICE_LOCK:
        timestamps = _RATE_LIMITS[key]
        _RATE_LIMITS[key] = [t for t in timestamps if now - t < window_seconds]
        if len(_RATE_LIMITS[key]) >= max_attempts:
            return True, int(window_seconds - (now - _RATE_LIMITS[key][0]))
        _RATE_LIMITS[key].append(now)
        return False, 0
