from rest_framework import serializers
from user.models import *
#from django.utils.timezone import datetime
import datetime
import logging,re
from rest_framework.response import Response
from rest_framework import status
from PIL import Image
#from .pagination import RestoPagination

logger = logging.getLogger('user')

class RestoListSerializer(serializers.ModelSerializer):
    logger.info("in serializer")
    is_open_now = serializers.SerializerMethodField()

    class Meta:
        model = RestrauntModel
        fields = ['id','name','description','cuisine_type','address',
                  'phone_number','email','logo','banner','delivery_fee',
                  'is_open_now','minimum_order',
                  'average_rating','total_reviews']
    
    def get_is_open_now(self,obj): #TO CHECK IF THE RESTO IS OPEN OR NOT AT GIVEN TIME
        logger.info(f"======================{datetime.datetime.now().time()}=================")
        if obj.opening_time <= datetime.datetime.now().time() <= obj.closing_time:
            logger.info('Restro is Open')
            return True
        logger.info('Restro is Closed')
        return False

    
class RestoCreateSerializer(serializers.ModelSerializer):
    # logger.info('Starting restro Create serializer')
    
    is_open = serializers.SerializerMethodField()

    def get_is_open(self,obj):
        logger.info(f"Current Time : ---- {datetime.datetime.now().time()}")
        print('Starting restro Create serializer')
        print(type(obj.opening_time))
        if obj.opening_time <= datetime.datetime.now().time() <= obj.closing_time:
            logger.info('Restro is Open')
            return True
        logger.info('Restro is Closed while being registered')
        return False 
    
    def validate_logo(self,value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Logo must be under 5MB")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")
            logger.info(f"logo validated: {value.name}")
        return value
    def validate_banner(self,value):
        if value:
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Banner must be under 10MB")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")
            logger.info(f"banner validated: {value.name}")
        return value


    class Meta:

        fields = ['owner','name','description','cuisine_type','address','phone_number','email','logo','banner',
                  'opening_time','closing_time','delivery_fee','minimum_order','is_open']
        read_only_fields = ['owner']

        # 'opening_time','closing_time','delivery_fee','minimum_order','is_open',
        #          'latitude','longitude']

        model = RestrauntModel
    
    def validate_phone_number(self,value):
        regexf = r'^\+?1?\d{9,15}$'
        if not re.match(regexf,value):
            raise serializers.ValidationError("Please enter the phone number in proper format")
        logger.info("regx matched succesful")
        return value
    
class RestoUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['logo','banner','minimum_order','opening_time','closing_time']
        model = RestrauntModel
    
    def validate_logo(self,value):
        if value:
            if value.size > 5*1024*1024:
                raise serializers.ValidationError("Image size cannot exceed 5mb")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")
        logger.info("image validated")
        logger.info(value)
        return value
    
    def validate_banner(self,value):
        if value:
            if value.size > 5*1024*1024:
                raise serializers.ValidationError("Image size cannot exceed 5mb")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")
        logger.info("image validated")
        logger.info(value)
        return value


    
        
class MenuItemSerializer(serializers.ModelSerializer):
    #restaurant = RestoSerializer()
    class Meta:
        fields = ['id','name','description','price','category','dietary_info','is_available','preparation_time']
        model = MenuItem
        #depth = 0

class RestoSerializer(serializers.ModelSerializer):
    menu = MenuItemSerializer(many=True)
    class Meta:
        fields = ['name','description','cuisine_type','is_open','opening_time','closing_time','menu','review_for']
        model = RestrauntModel
    
class MenuListSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['name','description','price','category','dietary_info','is_available','preparation_time']
        model = MenuItem

class MenuUSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['name','description','price','category','dietary_info','is_available','preparation_time','foodimage']
        model = MenuItem
    
    def validate_foodimage(self,value):
        logger.info("===========================")
        logger.info("CV.1 testing image")
        logger.info(value)
        logger.info("============================")
        if value:
            if value.size > 5*1024*1024:
                raise serializers.ValidationError("Image size cannot exceed 5mb")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")

        logger.info("image validated")
        logger.info(value)
        return value


class MenuSerializer(serializers.ModelSerializer):
    restoid = serializers.IntegerField()  
    
    class Meta:
        fields = ['restoid','foodimage','name','description','price','category','dietary_info','is_available','preparation_time']
        model = MenuItem


    def validate_foodimage(self,value):
        logger.info("===========================")
        logger.info("CV.1 testing image")
        logger.info(value)
        logger.info("============================")
        if value:
            if value.size > 5*1024*1024:
                raise serializers.ValidationError("Image size cannot exceed 5mb")
            ext = value.name.split('.')[-1].lower()
            if ext not in ['jpg','jpeg','png']:
                raise serializers.ValidationError("Only jpg, jpeg, png allowed")

        logger.info("image validated")
        logger.info(value)
        return value

    def validate_restoid(self,value):
        logger.info(" CV.2 =============================")
        logger.info(value)
        id = self.context.get('request').user.id
        try:
            self.resto = RestrauntModel.objects.filter(owner_id=id).get(id=value)
        except RestrauntModel.DoesNotExist:
            raise serializers.ValidationError("Please enter the restaurant which you own and does exits")
        logger.info(self.resto)
        logger.info(id)
        # print(type(owner))
        # print(restaurant__owner)
        logger.info(value)
        logger.info("CV.2 DONE =============================")
        #value = self.resto
        return value
    
