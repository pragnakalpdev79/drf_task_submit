from django.contrib import admin
from .models import *

@admin.register(CustomUser)
class CustomUser(admin.ModelAdmin):
    list_display = ('email','username','first_name','last_name','utype','phone_number','created_at','updated_at')
    ordering = ['-created_at']

@admin.register(CustomerProfile)
class CustomerProfile(admin.ModelAdmin):
    list_display = ('user','total_orders','loyalty_points','avatar')
    ordering = ['-created_at']

@admin.register(DriverProfile)
class DriverProfile(admin.ModelAdmin):
    list_display =('user','vehicle_type','vehicle_number','license_number','average_rating','total_deliveries','avatar')
    ordering = ['-created_at']

@admin.register(address)
class Address(admin.ModelAdmin):
    list_display = ('adrname','address','is_default','adrofuser','id','latitude','longitude','location')
    ordering = ['-created_at']

@admin.register(RestrauntModel)
class RestrauntModel(admin.ModelAdmin):
    list_display = ('name','email','phone_number','owner','cuisine_type','description','id','location')
    ordering = ['-created_at']


@admin.register(MenuItem)
class MenuItem(admin.ModelAdmin):
    list_display = ('name','restaurant','category','description','id')
    ordering = ['-created_at']



admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)