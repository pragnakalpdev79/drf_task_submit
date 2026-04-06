from django.contrib import admin
from django.urls import path,include
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


urlpatterns = [
    #FOR ADMIN ONLY
    path('foradmin/user/delete/<str:uname>',DeleteUser.as_view(),name='delete_user'),
    path('foradmin/user/restore/<str:uname>',RestoreDeletedUserView.as_view(),name='restore_deleted'),
    #USER AUTHENTICATION VIEWS
    path('auth/register/',UserRegisterationView.as_view(),name='register'), #REGISTER NEW USERS HERE WITH BASIC DETAILS
    path('auth/login/',UserLoginView.as_view(),name='login'),
    path('auth/logout/',UserLogoutView.as_view(),name='logout'),
    #VIEWS FOR JWT
    path('auth/token/',TokenObtainPairView.as_view(),name='token_obtain_pair'), #LOGIN-RETURNS TOKEN
    path('auth/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'), #REFRESH
    path('auth/token/verify/',TokenVerifyView.as_view(),name='token_verify'), #VERIFY
]