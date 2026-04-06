from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'address',AddressViewSet,basename='address')


urlpatterns = [
    #PROFILE VIEWS
    path('profiles/customer/myprofile',CustomerProfileView.as_view(),name='customer_profile'),
    path('profiles/driver/myprofile',DriverProfileView.as_view(),name='driver_profile'),
    path('',include(router.urls)),
   
]