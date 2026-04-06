# Standard Library Imports
import logging
from datetime import timedelta

# Third-Party Imports (Django)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.response import Response

# Local Imports
from .throttles import *
from user.models import *
from .filters import OrderFilter,ReviewFilter 
from user.permissions import IsRestaurantOwner,IsCustomer,IsDriver,IsRestaurantOwnerOrDriver
from .serializers import *
from .pagination import OrdersPagination,ReviewPagination

logger = logging.getLogger('user')

extrap = extend_schema(
        tags=["extra"],
    )

#===============================================================================================
# 1. CART VIEWSET - add or remove or view cart items
@extend_schema_view(
    addtocart=extend_schema(
        summary=" C.1Add to cart",
        description="Add an item to the cart before checkout to place order.",
        tags=["Cart"],
    ),
    mycart=extend_schema(
        summary="C.2 View cart with total",
        description="This endpoint returns whatever is in the cart and empty if not",
        tags=["Cart"],
    ),
    clear=extend_schema(
        summary=" C.3 Empty Cart",
        description="Remove Everything from the cart",
        tags=["Cart"],
    ),
    checkout=extend_schema(
        summary=" C.4 Checkout ",
        description="Confirm Payment here with confirm=true used as mock payment",
        tags=["Cart"],
    ),
    destroy = extrap,
    partial_update = extrap,
    update = extrap,
    retrive = extrap,
    create = extrap,
    list = extrap,
    )
class CartViewSet(viewsets.ModelViewSet):
    """
    Cart View set has the following functions
    1. Menu-items can be addes to the cart with post request
    2. Cart can be viewed
    3. Clear cart
    4. checkout -- 
        4.1 if confirm= False it will just show cart total and all
        4.2 if confirm= True it acts as mock payment and converts cart to order
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsCustomer]
    throttle_classes = [OrderCreateT]
    throttle_scope = 'checkout'
    
    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related('menu_item')

    def perform_create(self,serializer):
        serializer.save(user=self.request.user)
        logger.info(f"===item added to cart by {self.request.user.email}===")

    #==================================================================================
    # 1.1 add to cart - if item already exists just update quantity
    @action(detail=False,methods=['post'])
    def addtocart(self,request):
        logger.info("1.ADD TO CART VIEW")
        menu_item_id = request.data.get('menu_item')
        quantity = int(request.data.get('quantity',1))
        logger.info(f"1.1===adding item {menu_item_id} to cart===")

        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
            
        except MenuItem.DoesNotExist:
            logger.info("Menu_item does not exists")
            return Response({'error':'menu item not found'},status=status.HTTP_404_NOT_FOUND)

        if not menu_item.is_available:
            return Response({'error':f'{menu_item.name} is not available right now'},status=status.HTTP_404_NOT_FOUND)

        existing = CartItem.objects.filter(user=request.user,menu_item=menu_item).first()

        if existing:
            existing.quantity += quantity
            existing.save(update_fields=['quantity'])
            logger.info(f"1.2 ===updated quantity to {existing.quantity}===")
            serializer = CartItemSerializer(existing)

        else:
            cart_item = CartItem.objects.create(user=request.user,menu_item=menu_item,quantity=quantity)
            serializer = CartItemSerializer(cart_item)
            logger.info(f"1.2 Menu-Item added to the cart")

        return Response({
            'message': 'item added to cart',
            'item': serializer.data,
        },status=status.HTTP_202_ACCEPTED)
    


    #==================================================================================
    # 1.2 view full cart with total
    @action(detail=False,methods=['get'])
    def mycart(self,request):
        items = self.get_queryset()
        serializer = CartItemSerializer(items,many=True)
        cart_total = sum(item.menu_item.price * item.quantity for item in items)
        return Response({
            'items': serializer.data,
            'cart_total': cart_total,
            'item_count': items.count(),
        })
    


    #==================================================================================
    # 1.3 clear the ENTIRE CART
    @action(detail=False,methods=['delete'])
    def clear(self,request):
        count = CartItem.objects.filter(user=request.user).delete()[0] 
        logger.info(f"===cart cleared, {count} items removed===")
        return Response({'message':f'cart cleared, {count} items removed'})
    
    #==================================================================================
    # 1.4 CHECKOUT - CONVERT CART TO ORDER MOCK PAYMENT
    @action(detail=False,methods=['post'],throttle_classes=[OrderCreateT])
    def checkout(self,request):
        logger.info(f"===checkout started for {request.user.email}===")
        cart_items = CartItem.objects.filter(user=request.user).select_related('menu_item','menu_item__restaurant')

        if not cart_items.exists():
            return Response({'error':'cart is empty'},status=status.HTTP_400_BAD_REQUEST)

        restaurants = set(item.menu_item.restaurant_id for item in cart_items)
        if len(restaurants) > 1:
            return Response({'error':'all items must be from same restaurant'},status=status.HTTP_400_BAD_REQUEST)

        restaurant = cart_items.first().menu_item.restaurant
       
        cart_total = sum(item.menu_item.price * item.quantity for item in cart_items)

        if cart_total < restaurant.minimum_order:
            return Response({
                'error':f'minimum order is Rs.{restaurant.minimum_order}, your cart is Rs.{cart_total}'
            },status=status.HTTP_400_BAD_REQUEST)

        #get delivery address
        try:
            dadr = request.user.customer_profile.default_adress
            tadr = dadr.address
        except Exception:
            return Response({'error':'please set a default address first'},status=status.HTTP_400_BAD_REQUEST)

        special = request.data.get('special_instructions','')
        confirm = request.data.get('confirm',False)

        if not confirm:

            if restaurant.location and dadr.location:
                logger.info("resto location available")
                distance_m = restaurant.location.distance(dadr.location) * 100000
                distance_km = distance_m / 1000
                travel_min = max(int((distance_km / 40) * 60),5)
                eta_display = f"{travel_min + 15} minutes"
                distance_display = f"{distance_km:.1f} km"
            else:
                logger.info("no resto location")
                eta_display = "~30 minutes"
                distance_display = "unknown"
            
            return Response({
                'message': 'review your order and send confirm=true to place',
                'restaurant': restaurant.name,
                'items': CartItemSerializer(cart_items,many=True).data,
                'cart_total': cart_total,
                'delivery_fee': restaurant.delivery_fee,
                'delivery_address': dadr.address,
                'estimated_delivery': eta_display,
                'distance': distance_display,
            })

        #confirmed - creating the order
        logger.info("===order confirmed, creating===")
        order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            delivery_address=dadr,
            special_instructions=special,
            adratorder=tadr,
        )

        #converting cart items to order items
        for ci in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=ci.menu_item,
                quantity=ci.quantity,
                uprice=ci.menu_item.price,
            )
            logger.info(f"item: {ci.menu_item.name} * {ci.quantity} at the price {ci.menu_item.price}")

        order.calculate_total()
        
        order.calculate_eta()
        logger.info(f"ETA: {order.estimated_delivery_time}")

        #clear cart
        cart_items.delete()
        logger.info(f"===order {order.order_number} placed, cart cleared===")

        return Response({
            'message': 'order placed successfully!',
            'order': OrderSerializer(order).data,
        },status=status.HTTP_201_CREATED)






#===============================================================================================
# ORDER VIEWSET - view/manage orders
@extend_schema_view(
    update_status = extend_schema(
        summary=" O.1 UPDATE ORDER STATUS",
        description="Update the order status from confirmed to delivered,can be accessed by driver and restaurant owners",
        auth=[{"tokenAuth": [], }],
        tags=["Order"],
    ),
    assign_driver=extend_schema(
        summary=" O.2 Assign orders to driver",
        description="Orders can accept the new orders from here order id must be passed into request",
        auth=[{"tokenAuth": [], }],
        tags=["Order"],
    ),
    cancel=extend_schema(
        summary=" O.3 Cancel Order",
        description="Cancel order from this endpoint if allowed at given time",
        auth=[{"tokenAuth": [], }],
        tags=["Order"],
    ),
    active=extend_schema(
        summary=" O.4 List of active orders of user",
        description="Returns active orders of logged in user -- for customers only",
        auth=[{"tokenAuth": [], }],
        tags=["Order"],
    ),
    history=extend_schema(
        summary=" O.5 Past orders",
        description="Returns Customer's past completed orders -- for customers only",
        auth=[{"tokenAuth": [], }],
        tags=["Order"],
    ),
    destroy = extrap,
    partial_update = extrap,
    update = extrap,
    retrive = extrap,
    create = extrap,
    list = extrap,
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    Order Viewset once the order is placed has the following functions
    1. Update order status by resto and driver
    2. assign driver to order
    3. cancel order
    4. list all active orders
    5. list all past orders
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter 
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter] 
    search_fields = ['order_number'] 
    ordering_fields = ['created_at','total_amount'] 
    ordering = ['-created_at'] 

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.select_related('customer','restaurant','driver').prefetch_related('item_for__menu_item')
        #THIS VIEW WILL BE USED BY ALL 3  
        if self.action == "assign_driver":
            return qs
        if user.check_if_customer: 
            return qs.filter(customer=user)
        elif user.check_if_driver:
            print("driver")
            return qs.filter(driver=user)
        elif user.check_if_restaurant:
            return qs.filter(restaurant__owner=user)

    #===============================================================================================
    # O.1 STATUS UPDATE
    @action(detail=True,methods=['patch'],permission_classes=IsRestaurantOwnerOrDriver)
    def update_status(self,request,pk=None):
        order = self.get_queryset().get(order_number=pk)
        logger.info(f"===status update for order {order.order_number}===")
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order':order,'request':request}
        )
        logger.info("validating with serializer")
        serializer.is_valid(raise_exception=True)
        logger.info("validated with serializer")
        new_status = serializer.validated_data['status']
        logger.info("validating with serializer updated status in validated data")
        try:
            order._transition(new_status)
            logger.info("worked")
            return Response(OrderSerializer(order).data)
        except Exception as e:
            logger.info("did not work")
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)

    #===============================================================================================
    # O.2 ASSIGN DRIVER
    @action(detail=True,methods=['post'])
    def assign_driver(self,request,pk=None):
        logger.info(pk)
        order = self.get_queryset().get(order_number=pk)
        logger.info(order)
        #order = order.first()
        print("order",order) 
        logger.info(self.request.user.utype)
        logger.info(f"Assign driver request for order -- {order}")
        logger.info(f"Assign driver request for or    der -- {order.customer_id}")
        driver_id = request.data.get('driver_id')
        logger.info(f"===assigning driver {driver_id}===")
        try:
            driver = CustomUser.objects.get(id=driver_id,utype='d')
            dp = DriverProfile.objects.get(user_id=driver_id)
            if not dp.is_available:
                return Response({'error':'driver is busy'},status=status.HTTP_400_BAD_REQUEST)
            
            order.driver = driver
            order.save(update_fields=['driver'])
            dp.is_available = False
            dp.save(update_fields=['is_available'])

            return Response({'message':f'driver {driver.first_name} assigned'})
        
        except CustomUser.DoesNotExist:
            return Response({'error':'driver not found'},status=status.HTTP_404_NOT_FOUND)
    #===============================================================================================
    # O.3 CANCEL ORDER
    @action(detail=True,methods=['post'])
    def cancel(self,request,pk=None):
        order = self.get_queryset().get(order_number=pk)
        print(order)
        if not order.is_cancellable:
            return Response({'error':'cant cancel this order anymore'},status=status.HTTP_400_BAD_REQUEST)
        try:
            order.rreject()
            if order.driver:
                dp = order.driver.driver_profile
                dp.is_available = True
                dp.save(update_fields=['is_available'])

            return Response({'message':'order cancelled'})
        
        except Exception as e:
            return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    #=======================================
    #  O.4 LIST ALL ACTIVE ORDERS
    @action(detail=False,methods=['get'],pagination_class=OrdersPagination)
    def active(self,request):
        qs = self.get_queryset().exclude(status__in=['pd','co','pr','rd','pu'])
        qs = self.filter_queryset(qs) 
        page = self.paginate_queryset(qs) 
        if page is not None:
            return self.get_paginated_response(OrderSerializer(page, many=True).data)
        return Response(OrderSerializer(qs,many=True).data)

    #=======================================
    # O.5  LIST ALL ORDERS
    @action(detail=False,methods=['get'],pagination_class=OrdersPagination)
    def history(self,request):
        qs = self.get_queryset().filter(status__in=['dl','cd'])
        qs = self.filter_queryset(qs) 
        page = self.paginate_queryset(qs) 
        if page is not None:
            return self.get_paginated_response(OrderSerializer(page, many=True).data)
        return Response(OrderSerializer(qs,many=True).data)

#===============================================================================================
# REVIEW VIEWSET
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    #throttle_classes = [ReviewCreateT]
    pagination_class = ReviewPagination
    filterset_class = ReviewFilter 
    filter_backends = [DjangoFilterBackend,filters.OrderingFilter] 
    ordering_fields = ['created_at','rating'] 
    ordering = ['-created_at'] 
    
    def get_throttles(self):
        if self.action == 'create':
            return [ReviewCreateT()]
        return super().get_throttles()

    def get_queryset(self):
        qs = Review.objects.select_related('customer','restaurant','menu_item','order')
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        return qs

    def perform_create(self,serializer):
        serializer.save(customer=self.request.user)
        logger.info(f"===review created by {self.request.user.email}===")
