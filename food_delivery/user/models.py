# Standard Library Imports
from __future__ import unicode_literals
import uuid,logging,datetime
from decimal import Decimal
from datetime import timedelta


# Third-Party Imports (Django)
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.core.validators import RegexValidator,MaxValueValidator,MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg,Sum,F
from django.db.models import Manager as GeoManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

        
        


logger = logging.getLogger('user')

class TimestampedModel(models.Model):
    """
    Base Class for all models which need created and updated at field
    """
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True 



############################################################################
#  0. USER MANAGER FOR CUSTOMUSER MODEL
class MyUserManager(BaseUserManager):


    # 0.1 FUNCTION TO HANDLE NEW NORMAL USER CREATION
    def create_user(self,email,password=None,**extra_fields):

        #logger.info("p6-create function inside usermanager ")
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        #logger.info("----p6.1-email checkd -----")
        user = self.model(email=email,**extra_fields)
        #logger.info("----p6.2-details stored -----")
        user.set_password(password)
        #logger.info("----p6.3-password stored-----")
        user.save(using=self.db)
        #logger.info("----p6.4-user saved-----")
        return user
    

    # 0.2 FUNCTION TO HANDLE NEW ADMIN/SUPERUSER CREATION 
    def create_superuser(self,email,password=None,**extra_fields):

        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active',True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))
        
        return self.create_user(email,password,**extra_fields)
    
    
    # 0.3 USING ONLY NON-DELETED USERS
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    




############################################################################
#  1. MAIN USER MODEL EXTENDED FROM ABSTRACTUSER
class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False) #UUID
    email = models.EmailField(unique=True) #UNIQUE EMAIL
    first_name = models.CharField(max_length=20) # FIRST NAME
    last_name = models.CharField(max_length=20) # LAST NAME
    created_at = models.DateTimeField(auto_now_add=True) # CREATED AT
    updated_at = models.DateTimeField(auto_now=True) # UPDATED AT
    USER_TYPE = ( 
        ('c','Customer'),
        ('r','Restaurant Owner'),
        ('d','Delivery Driver   '),
    )
    utype = models.CharField(max_length=1,choices=USER_TYPE,blank=True,default='c',help_text='User Type') #USER TYPE
    deleted_at = models.DateTimeField(null=True,blank=True)
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be entered in the format: "+999999999".Up to 15 digits allowed.' 
        )],
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name','utype','phone_number']
    objects = MyUserManager()
    all_objects = models.Manager()

    # METHODS TO CHECK TYPE OF USER
    @property
    def check_if_customer(self):
        result = (self.utype == 'c')
        return result
    
    @property
    def check_if_restaurant(self):
        result = (self.utype == 'r')
        return result
    
    @property
    def check_if_driver(self):
        result = (self.utype == 'd')
        return result
    
    #SOFT DELETE AND USER RESTORE FROM LEVEL 3B SOFT DELETE CODE
    @property
    def delete(self,using=None,keep_parents=False):
        self.deleted_at = timezone.now()
        logger.info("User deleted")
        self.save() #overrides default delete method

    @property
    def restore(self):
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    class Meta: 
        permissions = [
            ('IsOwnerOrReadOnly',"AA owner can edit/delete, others read-only"),
            ('IsRestaurantOwner',"AA only restaurant owner can edit restaurant and menu items"),
            ('IsCustomer',"AA only customers can place orders and write reviews"),
            ('IsDriver',"AA only drivers can update delivery status and location"),
            ('IsOrderCustomer',"AA only order customer can view order details"),
            ('IsRestaurantOwnerOrDriver',"AA restaurant owner or assigned driver can update order status"),
        ]






############################################################################
#  2. ADDRESS MODEL TO STORE ALL ADDRESSES
class address(TimestampedModel):
    adrname = models.CharField(max_length=60,unique=True,help_text='Short name to identify the adress')
    address = models.TextField(help_text='Your full address')
    is_default = models.BooleanField()
    adrofuser = models.ForeignKey('CustomUser',on_delete=models.CASCADE,related_name="user_s_adress")
    latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,help_text='Latitude')
    longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,help_text='Longitude')
    location = gis_models.PointField(srid=4326,null=True,blank=True,help_text='coordinates for distance calculation')


    def save(self,*args,**kwargs):
        if self.is_default:
            usradrs = address.objects.filter(adrofuser=self.adrofuser)
            usradrs.update(is_default=False)
        if self.latitude and self.longitude and not self.location:
            self.location = Point(float(self.longitude),float(self.latitude),srid=4326)
            logger.info(f"location point created: {self.location}")
        super().save(*args,**kwargs)

    def __str__(self):
        return f"User : {self.adrofuser}, Adress saved as : {self.adrname}, Full Address:  {self.address}"








############################################################################
#  3.CUSTOMER PROFILE
class CustomerProfile(TimestampedModel):
    user = models.OneToOneField('CustomUser',on_delete=models.RESTRICT,related_name='customer_profile',primary_key=True)
    avatar = models.ImageField(upload_to='user_avatars/',blank=True,null=True)
    loyalty_points = models.IntegerField(default=0)

    @property
    def default_adress(self):
        defadr = address.objects.get(adrofuser=self.user,is_default=True)
        return defadr

    @property
    def saved_addresses(self):
        alladrs = address.objects.filter(adrofuser=self.user)
        return alladrs

    @property
    def total_orders(self):
        return self.user.order_for.count()
    
    @property
    def total_spend(self):
        spend = self.user.order_for.filter(status='dl')
        spend = spend.aggregate(total=Sum('total_amount'))
        if spend['total']:
            return spend['total']
        return Decimal('0.00')
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"







############################################################################
#  4.DRIVER PROFILE
class DriverProfile(TimestampedModel):
    user = models.OneToOneField('CustomUser',on_delete=models.RESTRICT,related_name='driver_profile')
    avatar = models.ImageField(upload_to='user_avatars/',blank=True,null=True)
    VTYPE = (
        ('b','Bike'),
        ('s','Scooter'),
        ('c','Car'),
    )
    vehicle_type = models.CharField(max_length=1,choices=VTYPE,blank=True,default='b',help_text="Delivery partner's Vehicle Type")
    vehicle_number = models.CharField(max_length=10,unique=True)
    license_number = models.CharField(max_length=10,unique=True)
    is_available = models.BooleanField(default=True)
    total_deliveries = models.IntegerField(blank=True,null=True)
    average_rating = models.DecimalField(max_digits=2,decimal_places=1,default=0)

    def update_availability(self,available=True):
        #changing availability directly from this function
        self.is_available = available
        self.save(update_fields=['is_available'])
        logger.info(f"driver availability set to {available}")


    def get_delivery_stats(self):
        # get all delivered orders of requested user
        delivered = Order.objects.filter(driver=self.user,status='dl').count()
        logger.info(f"delivery stats for {self.user.email}: {delivered}")
        return {
            'total_deliveries': delivered,
            'average_rating': self.average_rating,
            'is_available': self.is_available,
        }







############################################################################
#  5.Restraunt-Model
class RestrauntModel(TimestampedModel):
    owner = models.ForeignKey('CustomUser',on_delete=models.RESTRICT,related_name='restraunt_owner')
    name = models.CharField(max_length=50)
    description = models.TextField()
    CC = (
        ('it','Italian'),
        ('ch','Chinese'),
        ('in','Indian'),
        ('me','Mexican'),
        ('am','American'), 
        ('ja','Japanese'),
        ('th','Thai'),
        ('md','Mediterranean'),
    )
    cuisine_type = models.CharField(max_length=2,choices=CC,help_text='Available Cuisine')
    address = models.TextField()
    phone_number = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message='Phone number must be entered in the format: "+999999999".Up to 15 digits allowed.' ,
        )],)
    email = models.EmailField(unique=True) 
    logo = models.ImageField(upload_to='logos/',blank=True,null=True)
    banner = models.ImageField(upload_to='banners/',blank=True,null=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=False)
    delivery_fee = models.DecimalField(max_digits=4,decimal_places=2)
    minimum_order = models.DecimalField(default=0,decimal_places=0,max_digits=3)
    average_rating = models.DecimalField(max_digits=2,default=0,decimal_places=1)
    total_reviews = models.IntegerField(null=True,blank=True)
    deleted_at = models.DateTimeField(null=True,blank=True)
    latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,help_text='Latitude of restaurant')
    longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,help_text='Longitude of restaurant')
    location = gis_models.PointField(srid=4326,null=True,blank=True,help_text='GPS coordinates for distance calculation')

    def save(self,*args,**kwargs):
        #=====================================
        # AUTO-CREATE POINT FROM LAT/LNG
        #=====================================
        if self.latitude and self.longitude and not self.location:
            self.location = Point(float(self.longitude),float(self.latitude),srid=4326)
            logger.info(f"restaurant location point created: {self.location}")
        super().save(*args,**kwargs)

    def is_currently_open(self):
        now = datetime.datetime.now().time()
        result = self.opening_time <= now <= self.closing_time
        logger.info(f"{self.name} is_currently_open: {result}")
        return result
    
    def update_average_rating(self):
        avg = self.review_for.aggregate(avg=Avg('rating'))['avg']
        if avg:
            self.average_rating = round(avg,1)
            self.total_reviews = self.review_for.count()
            self.save(update_fields=['average_rating','total_reviews'])
            logger.info(f"updated rating for {self.name} to {self.average_rating}")

    @property
    def delete(self,using=None,keep_parents=False):
        print("deleting")
        self.deleted_at = timezone.now()
        self.save()
    
    @property
    def restore(self):
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"{self.name}"







############################################################################
#  6. Menu-Items Model
class MenuItem(TimestampedModel):
    restaurant = models.ForeignKey('RestrauntModel',on_delete=models.CASCADE,related_name='menu')
    name = models.CharField(max_length=50)
    description = models.TextField()
    price = models.DecimalField(max_digits=5,decimal_places=2)
    CAC = (
        ('a','Appteizer'),
        ('m','Main Course'),
        ('d','Desert'),
        ('b','Beverage'),
        ('s','Side Dish'),
    )
    category = models.CharField(
        max_length = 1,
        choices = CAC,
        help_text = 'Available Catagories',
    )
    DIC = (
        ('v1','Vegetarian'),
        ('v2','Vegan'),
        ('gf','Gluten-Free'),
        ('df','Dairy-Free'),
        ('no','None'),
    )
    dietary_info = models.CharField(
        max_length=2,
        choices = DIC,
        help_text= 'Diteray information',
    )
    is_available = models.BooleanField(default=True)
    preparation_time = models.PositiveIntegerField(default=3)


    def file_path(self):
        return f"{self.name}/menu_items"
    
    foodimage = models.ImageField(upload_to=file_path,blank=True,null=True)

    def __str__(self):
        return f"{self.name}"







############################################################################
#  7. Order Model
class Order(TimestampedModel):
    customer = models.ForeignKey('CustomUser',on_delete=models.DO_NOTHING,related_name='order_for',db_index=True)
    restaurant = models.ForeignKey('RestrauntModel',on_delete=models.DO_NOTHING,related_name='order_by',db_index=True)
    driver = models.ForeignKey('CustomUser',on_delete=models.DO_NOTHING,related_name='deliver_by',null=True)
    order_number = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    STATE_PD = 'pd'
    STATE_CO = 'co'
    STATE_PR = 'pr'
    STATE_RD = 'rd'
    STATE_PU = 'pu'
    STATE_DL = 'dl'
    STATE_CD = 'cd'

    __current_status = None

    SC = (
        (STATE_PD,'Pending'),
        (STATE_CO,'Confiremd'),
        (STATE_PR,'Preparing'),
        (STATE_RD,'Ready'),
        (STATE_PU,'Picked Up'),
        (STATE_DL,'Delivered'),
        (STATE_CD,'Cancelled'),
    )
    TRANSITIONS = {
        STATE_PD: [STATE_CO,STATE_CD],
        STATE_CO: [STATE_PR,STATE_CD],
        STATE_PR: [STATE_RD,STATE_CD],
        STATE_RD: [STATE_PU,STATE_CD],
        STATE_PU: [STATE_DL],
        STATE_DL: [],
        STATE_CD: [],
    }
    status = models.CharField(
        max_length=2,
        choices= SC,
        help_text = 'Order Status',
        db_index=True,
        default=STATE_PD,
    )
    adratorder = models.TextField()
    delivery_address = models.ForeignKey('address',on_delete=models.DO_NOTHING,related_name='delivery_adress')
    subtotal = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    delivery_fee = models.DecimalField(max_digits=6,decimal_places=2,default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=6,decimal_places=2,default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    special_instructions = models.TextField(null=True,blank=True)
    estimated_delivery_time = models.DateTimeField(null=True,blank=True)
    actual_delivery_time = models.DateTimeField(null=True,blank=True)

    def calculate_total(self,tax_rate=Decimal('0.05')):
        self.subtotal = self.item_for.aggregate(
            total=Sum(F('uprice') * F('quantity'))
        )['total'] or Decimal('0.00')
        self.delivery_fee = self.restaurant.delivery_fee
        self.tax = (self.subtotal * tax_rate).quantize(Decimal('0.01'))
        self.total_amount = self.subtotal + self.delivery_fee + self.tax
        self.save(update_fields=['subtotal','delivery_fee','tax','total_amount'])
        logger.info(f"Order total:-- sub = {self.subtotal} ---- tax={self.tax} ----- total={self.total_amount}")

    def calculate_eta(self):
        """
        Calculate estimated delivery time based on distance between
        restaurant and delivery address using geodjango.
        Assumes 40 km/h average delivery speed.
        """
        logger.info("calculating ETA ")
        resto_location = self.restaurant.location
        delivery_location = self.delivery_address.location

        if not resto_location or not delivery_location:
            logger.info("location data not found")
            self.estimated_delivery_time = timezone.now() + timedelta(minutes=30) # 30 MIN DEFAULT 
            self.save(update_fields=['estimated_delivery_time'])
            return

        distance_m = resto_location.distance(delivery_location) * 100000  # degrees to meters approx
        distance_km = distance_m / 1000
        logger.info(f"distance: {distance_km:.2f} km")
        SPEED_KMH = 40
        travel_hours = distance_km / SPEED_KMH
        travel_minutes = max(int(travel_hours * 60),5)  # minimum 5 min
        max_prep = self.item_for.aggregate(
            max_prep=models.Max('menu_item__preparation_time')
        )['max_prep'] or 15
        logger.info(f"max prep time: {max_prep} min")
        total_minutes = travel_minutes + max_prep
        self.estimated_delivery_time = timezone.now() + timedelta(minutes=total_minutes)
        self.save(update_fields=['estimated_delivery_time'])
        logger.info(f"ETA == {self.estimated_delivery_time} ({total_minutes} min = {travel_minutes} travel + {max_prep} prep)")

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__current_status = self.status #INTIATED WITH PENDING ORDER STATUS
    
    def save(self, force_insert=False, 
             force_update=False, 
             using=None,
             update_fields=None): 
        # CHECKS IF THE MODEL IS BEING CREATED OR UPDATED
        #IF THE STATE IS CHANGED ITS UPDATED HENCE SKIP VALIDATION
        # self.status(pending) != self.__current_status(pending) which means it is not updated yet. hence False(Not Updated)
        logger.info("step1")
        allowed_next = self.TRANSITIONS.get(self.__current_status,[]) 
        logger.info("step2")
        updated = self.status != self.__current_status
        logger.info("step3")

        if self.pk and updated and self.status not in allowed_next:
            raise Exception("Invalid Transition.",self.status,allowed_next)
        
        logger.info("step4")

        if self.pk and updated:
            self.__current_status = self.status

        logger.info("step5")

        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
    
    def _transition(self,next_status):
        logger.info("step6")
        self.status = next_status
        logger.info("step7")
        if next_status == self.STATE_DL:
            self.actual_delivery_time = timezone.now()
        self.save()
        logger.info(f"Order {self.order_number} transitioned to {next_status}")

    def raccept(self,driver=None):
        self._transition(self.STATE_CO)

    def rreject(self):
        self._transition(self.STATE_CD)

    def confiremd(self):
        self._transition(self.STATE_PR)

    def readytop(self):
        self._transition(self.STATE_RD)

    def pickedup(self):
        self._transition(self.STATE_PU)

    def delivered(self):
        self._transition(self.STATE_DL)

    @property
    def is_cancellable(self):
        return self.status in [self.STATE_PD,self.STATE_CO,self.STATE_PR,self.STATE_RD]

    @property
    def is_completed(self):
        return self.status in [self.STATE_DL,self.STATE_CD]







############################################################################
#  8. Cart-Items Model
class CartItem(models.Model):
    user = models.ForeignKey('CustomUser',on_delete=models.CASCADE,related_name='user_cart')
    menu_item = models.ForeignKey('MenuItem',on_delete=models.DO_NOTHING,related_name='added_item')
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"This is {self.user}'s cart for - {self.menu_item} with quantity {self.quantity}"







############################################################################
#  9. Order-Item Model
class OrderItem(models.Model):
    order = models.ForeignKey('Order',on_delete=models.DO_NOTHING,related_name='item_for')
    menu_item = models.ForeignKey('MenuItem',on_delete=models.DO_NOTHING,related_name='item_from')
    quantity = models.PositiveIntegerField(blank=False,null=False)
    uprice = models.DecimalField(max_digits=5,decimal_places=2,help_text='snapshot of item price at order time')
    special_instructions = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" Order Item details : {self.menu_item} | Quantity : {self.quantity} | Special Instructions provided : {self.special_instructions}" 







############################################################################
#  10. Cart Model
class Review(TimestampedModel):
    customer = models.ForeignKey('CustomUser',on_delete=models.CASCADE,related_name='review_by')
    restaurant = models.ForeignKey('RestrauntModel',on_delete=models.CASCADE,related_name='review_for',null=True)
    menu_item = models.ForeignKey('MenuItem',on_delete=models.CASCADE,related_name='review_of',null=True)
    order = models.ForeignKey('Order',on_delete=models.CASCADE,related_name='order')
    rating = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    comment = models.TextField(null=True)

    def clean(self):
        if self.order.customer != self.customer:
            raise ValidationError("you can only review your own orders")
        if self.order.status != 'dl':
            raise ValidationError("can not review the orders which are not delivered")
        
    def __str__(self):
        return f"Review by {self.customer.email} for menu-item {self.menu_item} is {self.rating},which was order the {self.restaurant} "