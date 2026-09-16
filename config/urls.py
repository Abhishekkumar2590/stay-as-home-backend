from django.conf import settings
from django.contrib import admin
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.urls import include, path, re_path
from django.views.static import serve
from django.http import JsonResponse

admin.site.site_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

def admin_logout(request):
    auth_logout(request)
    return redirect(getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'))

def root_index(request):
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    return JsonResponse({
        'status': 'online',
        'service': 'QuickStay Hotel Management API Backend',
        'version': '1.0.0',
        'endpoints': {
            'hotels': '/api/hotels/',
            'rooms': '/api/rooms/',
            'bookings': '/api/bookings/',
            'feedbacks': '/api/feedbacks/',
            'kafka_health': '/api/kafka/status/',
            'kafka_test_publish': '/api/kafka/publish-test/',
            'analytics': '/api/analytics/summary/',
            'staff_management': '/manage/',
            'django_admin': '/admin/',
        },
        'frontend_url': frontend_url,
        'documentation': 'Append any endpoint above to this domain to access live REST data.',
    })

def redirect_to_api(target_path):
    def view(request, *args, **kwargs):
        return redirect(f'/api/{target_path}/', permanent=False)
    return view

def custom_404(request, exception=None):
    path = request.path
    if path.strip('/').startswith('hotels'):
        return redirect('/api/hotels/', permanent=False)
    if path.strip('/').startswith('rooms'):
        return redirect('/api/rooms/', permanent=False)
    if path.strip('/').startswith('bookings'):
        return redirect('/api/bookings/', permanent=False)
    if path.strip('/').startswith('feedbacks'):
        return redirect('/api/feedbacks/', permanent=False)
    if path.strip('/').startswith('manage'):
        return redirect('/manage/', permanent=False)
    if path.strip('/').startswith('admin'):
        return redirect('/admin/', permanent=False)

    return JsonResponse({
        'error': '404 Not Found',
        'message': f'The requested path "{path}" was not found on this API server.',
        'available_endpoints': {
            'hotels': '/api/hotels/',
            'rooms': '/api/rooms/',
            'bookings': '/api/bookings/',
            'feedbacks': '/api/feedbacks/',
            'kafka_health': '/api/kafka/status/',
            'analytics': '/api/analytics/summary/',
            'staff_management': '/manage/',
            'django_admin': '/admin/',
        },
        'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173'),
    }, status=404)

handler404 = custom_404

urlpatterns = [
    path('', root_index, name='root-index'),
    path('api', root_index, name='api-root-noslash'),
    path('hotels', redirect_to_api('hotels')),
    path('hotels/', redirect_to_api('hotels')),
    path('rooms', redirect_to_api('rooms')),
    path('rooms/', redirect_to_api('rooms')),
    path('bookings', redirect_to_api('bookings')),
    path('bookings/', redirect_to_api('bookings')),
    path('feedbacks', redirect_to_api('feedbacks')),
    path('feedbacks/', redirect_to_api('feedbacks')),
    path('admin/logout/', admin_logout, name='admin-logout'),
    path('admin/', admin.site.urls),
    path('manage/', include('bookings.management_urls')),
    path('api/', include('bookings.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
