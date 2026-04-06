from django.contrib import admin
from django.conf import settings
from django.urls import path,include,re_path
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('user.urls')),
    path('api/restaurants/',include('restaurants.urls')),
    path('api/profiles/',include('profiles.urls')),
    path('notification/',include('notification.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),   
    path('api/orders/',include('orders.urls')),

]

admin.site.site_title = 'Delivery system admin dahsboard'
admin.site.site_header = 'Delivery system admin'
admin.site.index_title = 'Dashboard'

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/",include("debug_toolbar.urls")),
        re_path(r'^silk/', include('silk.urls', namespace='silk')),
        # static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT),
        # static(settings.STATIC_URL,document_root=settings.STATIC_ROOT),
    ]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
