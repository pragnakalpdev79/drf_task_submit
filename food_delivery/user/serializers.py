# Standard Library Imports
import logging,re
# Third-Party Imports (Django)
from django.contrib.auth import authenticate
from rest_framework import serializers
# Local Imports
from .models import *


logger = logging.getLogger('user')


#===============================================================
# SIGN UP VIEW SERIALIZER
class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    """
    USED IN  USER SIGN UP/REGISTRATION VIEW
    - Validates Phone number
    - Validates 2 input passwords if they are same or not
    """
    
    password = serializers.CharField(min_length=8,)
    password_confirm = serializers.CharField(write_only=True)
    class Meta:
        model = CustomUser
        fields = ['username','email','phone_number','password','password_confirm','first_name','last_name','utype']
    
    def validate_phone_number(self,value):
        regexf = r'^\+?1?\d{9,15}$'
        if not re.match(regexf,value):
            raise serializers.ValidationError("Please enter the phone number in proper format")
        return value

    def validate(self,data): 
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords dont match")
        data.pop('password_confirm')
        return data

    def create(self,data):
        user = CustomUser.objects.create_user(**data)
        return user






#===============================================================
# LOGIN VIEW SERIALIZER
class CustomUserLoginSerializer(serializers.ModelSerializer):
    """
    Basic login serializer which validates email with authenticate()
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email','password']

    def validate(self,data):
        user = authenticate(email=data['email'],password=data['password'])
        if not user:
            # this will check both if user is deleted or user was never registered
            #  as queryset only considers the non-deleted users
            # and is_active too.
            logger.info(f'Requested User does not exist raising Validation Error      ')
            raise serializers.ValidationError("Please enter proper email and password")
        data['user'] = user
        return data
    



#===============================================================
# Restraunt SERIALIZER
class RestrauntSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestrauntModel
        fields = "__all__"


#===============================================================
# MenuItem SERIALIZER
class MenuItemSerilizer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"

#===============================================================
# OrderDetail SERIALIZER
class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
