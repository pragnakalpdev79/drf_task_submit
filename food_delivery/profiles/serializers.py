# Standard Library Imports
import logging,re
from PIL import Image

from rest_framework import serializers

from user.models import *


logger = logging.getLogger('user')

class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = address
        fields = ['id','adrname','address','is_default','latitude','longitude'] 


class CustomProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerProfile
        fields = ['user','avatar','total_orders','loyalty_points']
        read_only_fields = ['loyalty_points']

    
    def validate_avatar(self,value):
        if value:
            if value.size > 5*1024*1024:
                raise serializers.ValidationError("Image size cannot exceed 5mb")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")
        try:
            img = Image.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError("Invalid Image format")
        return value
        

class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = "__all__"