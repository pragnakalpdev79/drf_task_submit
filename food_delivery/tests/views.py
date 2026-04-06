import pytest
from django.contrib.auth.models import Group


# Third-Party Imports
from asgiref.sync import async_to_sync,sync_to_async
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import Group,Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework import status


# Local Imports
from notification.consumers import CustomerConsumer,OrderConsumer,RestoConsumer,DriverConsumer
from orders.consumers import OrderConsumer as RoomOrderConsumer
from user.models import *
from user.signals import send_noti_user

# #===============================================================================
# #===============================================================================
# # FIXTURES
# #===============================================================================

@pytest.fixture(autouse=True)
def create_groups(db):
    cgrps,created = Group.objects.get_or_create(name='Customers')
    Group.objects.get_or_create(name='RestrauntOwners')
    Group.objects.get_or_create(name='Drivers')
    print("groups created for test")
    content_type = ContentType.objects.get_for_model(CustomUser)
    customer_permissions = Permission.objects.filter(content_type=content_type,
                                                     codename__in =['IsCustomer'])
    cgrps.permissions.set(customer_permissions)
    

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def customer(db):
    user = CustomUser.objects.create_user(
        email='testcust@test.com',
        password='testpass123',
        username='testcust',
        first_name='Test',
        last_name='Customer',
        phone_number='+919999999990',
        utype='c'
    )
    print(f"created customer -- {user.has_perms}")
    grp = Group.objects.get(name='Customers')
    print(grp.permissions.all())
    user.groups.add(grp)
    return user

@pytest.fixture
def resto_owner(db):
    user = CustomUser.objects.create_user(
        email='testowner@test.com',
        password='testpass123',
        username='testowner',
        first_name='Test',
        last_name='Owner',
        phone_number='+919999999991',
        utype='r'
    )
    print(f"created resto owner -- {user}")
    
    return user

@pytest.fixture
def driver(db):
    user = CustomUser.objects.create_user(
        email='testdriver@test.com',
        password='testpass123',
        username='testdriver',
        first_name='Test',
        last_name='Driver',
        phone_number='+919999999992',
        utype='d'
    )

    print(f"created driver -- {user}")
    return user

@pytest.fixture
def restaurant(db,resto_owner):
    resto = RestrauntModel.objects.create(
        owner=resto_owner,
        name='Test Indianresto',
        description='testing food',
        cuisine_type='in',
        address='123 test Gandhinagar',
        phone_number='+918888888885',
        email='resto@test.com',
        opening_time='09:00:00',
        closing_time='23:00:00',
        is_open=True,
        delivery_fee=Decimal('30.00'),
        minimum_order=Decimal('100'),
    )
    print(f"created restaurant -- {resto}")
    return resto

@pytest.fixture
def menu_items(db,restaurant):
    item1 = MenuItem.objects.create(
        restaurant=restaurant,
        name='Paneer Butter Masala',
        description='paneer',
        price=Decimal('250.00'),
        category='m',
        dietary_info='v1',
        is_available=True,
    )
    item2 = MenuItem.objects.create(
        restaurant=restaurant,
        name='Dal Tadka',
        description='dal with tadka',
        price=Decimal('150.00'),
        category='m',
        dietary_info='v1',
        is_available=True,
    )
    item3 = MenuItem.objects.create(
        restaurant=restaurant,
        name='Gulab Jamun',
        description='dessert',
        price=Decimal('80.00'),
        category='d',
        dietary_info='no',
        is_available=False,
    )
    print(f"created 3 menu items for {restaurant.name}")
    return [item1,item2,item3]

@pytest.fixture
def customer_with_address(db,customer):
    #creating address for checkout
    adr = address.objects.create(
        adrname='Home',
        address='q123 adr ahmedbad',
        is_default=True,
        adrofuser=customer
    )
    print(f"address set for {customer.email} -- {adr}")
    return customer

# #===============================================================================
# #===============================================================================
# # 1. REGISTRATION TESTS
# #===============================================================================

@pytest.mark.django_db
class TestRegistration:
    #NORMAL REGISTRATION
    #DONE
    def test_customer_registration(self,api_client):
        print("=====test1 registration=====")
        data = {
            'email':'newcust@test.com',
            'username':'newcust',
            'password':'strongpass123',
            'password_confirm':'strongpass123',
            'first_name':'New',
            'last_name':'Customer',
            'phone_number':'+911234567890',
            'utype':'c'
        }
        response = api_client.post('/api/auth/register/',data,format='json')
        print(f"response -- {response.status_code}")
        print(response)
        assert response.status_code == 201
        assert 'access' in response.data
        assert 'refresh' in response.data
    #PASSWORD MISMATCH
    #DONE
    def test_registration_password_mismatch(self,api_client):
        print("=====test2 password mismatch=====")
        data = {
            'email':'fail@test.com',
            'username':'failuser',
            'password':'spass123',
            'password_confirm':'wpass123',
            'first_name':'Fail',
            'last_name':'User',
            'phone_number':'+911234567890',
            'utype':'c'
        }
        response = api_client.post('/api/auth/register/',data,format='json')
        print(f"response -- {response.status_code}")
        assert response.status_code == 400
    #DUPLICATE EMAIL
    #DONE
    def test_registration_duplicate_email(self,api_client,customer):
        print("=====test3 duplicate email=====")
        data = {
            'email':'testcust@test.com', #already exists
            'username':'anothercust',
            'password':'strongpass123',
            'password_confirm':'strongpass123',
            'first_name':'Another',
            'last_name':'Customer',
            'phone_number':'+911234567890',
            'utype':'c'
        }
        response = api_client.post('/api/auth/register/',data,format='json')
        print(f"response -- {response.status_code}")
        assert response.status_code == 400

#===============================================================================
# 2. CART TESTS
#===============================================================================

@pytest.mark.django_db
class TestCart:
#DONE
    def test_add_to_cart(self,api_client,customer,menu_items,create_groups):
        print("=====test4 add to cart=====")
        api_client.force_authenticate(user=customer)
        #print(customer.check_if_customer)
        print(customer.user_permissions) 
        print(customer.has_perm('user.IsCustomer'))
        print(menu_items[1].id)
        data = {'menu_item':menu_items[1].id,'quantity':2}
        print(data)
        response = api_client.post('/api/orders/cart/addtocart/',data,format='json')
        print(f"response -- {response.status_code}")
        print(response)
        assert response.status_code == 202
        assert response.data['message'] == 'item added to cart'
#DONE
    def test_add_unavailable_item(self,api_client,customer,menu_items):
        print("=====test5 unavailable item=====")
        api_client.force_authenticate(user=customer)
        data = {'menu_item':menu_items[2].id,'quantity':1} #gulab jamun is unavailable
        print(data)
        response = api_client.post('/api/orders/cart/addtocart/',data,format='json')
        print(response)
        print(f"response -- {response.status_code}")
        assert response.status_code == 404
        assert 'not available' in response.data['error']

#DONE
    def test_add_duplicate_item_increases_quantity(self,api_client,customer,menu_items):
        print("=====test6 duplicate item quantity update=====")
        api_client.force_authenticate(user=customer)
        data = {'menu_item':menu_items[0].id,'quantity':1}
        api_client.post('/api/orders/cart/addtocart/',data,format='json')
        #adding again
        response = api_client.post('/api/orders/cart/addtocart/',data,format='json')
        print(f"response -- {response.status_code}")
        #quantity should be 2 now
        cart = CartItem.objects.get(user=customer,menu_item=menu_items[0])
        print(f"cart quantity -- {cart.quantity}")
        assert cart.quantity == 2
#DONE
    def test_view_cart(self,api_client,customer,menu_items):
        print("=====test7 view my cart=====")
        api_client.force_authenticate(user=customer)
        #add items first
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':2},format='json')
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[1].id,'quantity':1},format='json')
        response = api_client.get('/api/orders/cart/mycart/')
        print(f"response -- {response.status_code}")
        print(f"cart total -- {response.data['cart_total']}")
        print(f"item count -- {response.data['item_count']}")
        assert response.status_code == 200
        assert response.data['item_count'] == 2
        assert float(response.data['cart_total']) == 650.00
#DONE
    def test_clear_cart(self,api_client,customer,menu_items):
        print("=====test8 clear cart=====")
        api_client.force_authenticate(user=customer)
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':1},format='json')
        response = api_client.delete('/api/orders/cart/clear/')
        print(f"response -- {response.status_code}")
        assert response.status_code == 200
        assert CartItem.objects.filter(user=customer).count() == 0
#DONE
    def test_unauthenticated_cart_access(self,api_client,menu_items):
        print("=====test9 no auth cart=====")
        response = api_client.get('/api/orders/cart/mycart/')
        print(f"response -- {response.status_code}")
        assert response.status_code in [401,403]


# #===============================================================================
# # 3. CHECKOUT TESTS
# #===============================================================================

@pytest.mark.django_db
class TestCheckout:
#DONE
    def test_checkout_preview(self,api_client,customer_with_address,menu_items):
        print("=====test10 checkout preview=====")
        api_client.force_authenticate(user=customer_with_address)
        #ADD ITEMS
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':2},format='json')
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[1].id,'quantity':1},format='json')
        #PREVIEW BEFOR PLACING- confirm=false
        response = api_client.post('/api/orders/cart/checkout/',{'confirm':False},format='json')
        print(f"response -- {response.status_code}")
        print(response.data)
        assert response.status_code == 200
        assert 'review your order' in response.data['message']
        assert 'delivery_fee' in response.data
        #cart should NOT be cleared yet
        assert CartItem.objects.filter(user=customer_with_address).count() == 2
#DONE
    def test_checkout_confirm(self,api_client,customer_with_address,menu_items):
        print("=====test11 checkout confirmed=====")
        api_client.force_authenticate(user=customer_with_address)
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':2},format='json')
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[1].id,'quantity':1},format='json')
        #confirm
        response = api_client.post('/api/orders/cart/checkout/',{'confirm':True},format='json')
        print(f"response -- {response.status_code}")
        print(response.data)
        assert response.status_code == 201
        assert 'order' in response.data
        #cart should be empty now
        assert CartItem.objects.filter(user=customer_with_address).count() == 0
        #order should exist
        assert Order.objects.filter(customer=customer_with_address).count() == 1
#DONE
    def test_checkout_empty_cart(self,api_client,customer_with_address):
        print("=====test12 empty cart checkout=====")
        api_client.force_authenticate(user=customer_with_address)
        response = api_client.post('/api/orders/cart/checkout/',{'confirm':True},format='json')
        print(f"response -- {response.status_code}")
        assert response.status_code == 400
        assert 'empty' in response.data['error']
#DONE
    def test_checkout_below_minimum(self,api_client,customer_with_address,menu_items):
        print("=====test13 below minimum order=====")
        api_client.force_authenticate(user=customer_with_address)
        #gulab jamun is 80rs, minimum order is 100
        #so adding an available cheap item
        cheap = MenuItem.objects.create(
            restaurant=menu_items[0].restaurant,
            name='Papad',
            description='just a papad',
            price=Decimal('20.00'),
            category='s',
            dietary_info='v1',
            is_available=True,
        )
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':cheap.id,'quantity':1},format='json')
        response = api_client.post('/api/orders/cart/checkout/',{'confirm':True},format='json')
        print(f"response -- {response.status_code}")
        assert response.status_code == 400
        assert 'minimum' in response.data['error']

#===============================================================================
# 4. ORDER STATUS TESTS
#===============================================================================

@pytest.mark.django_db
class TestOrderStatus:
    def _create_order(self,api_client,customer_with_address,menu_items):
        #helper -- creates an order via checkout
        api_client.force_authenticate(user=customer_with_address)
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':2},format='json')
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[1].id,'quantity':1},format='json')
        response = api_client.post('/api/orders/cart/checkout/',{'confirm':True},format='json')
        print(f"order created -- {response.data}")
        return response.data['order']['order_number']

#DONE
    def test_order_starts_as_pending(self,api_client,customer_with_address,menu_items):
        print("=====test14 order initial status=====")
        order_id = self._create_order(api_client,customer_with_address,menu_items)
        order = Order.objects.get(order_number=order_id)
        print(f"order status -- {order.status}")
        assert order.status == 'pd'

#DONE
    def test_order_has_correct_total(self,api_client,customer_with_address,menu_items,restaurant):
        print("=====test15 order total=====")
        order_id = self._create_order(api_client,customer_with_address,menu_items)
        order = Order.objects.get(order_number=order_id)
        #subtotal = 250*2 + 150*1 = 650
        print(f"subtotal -- {order.subtotal}")
        print(f"delivery_fee -- {order.delivery_fee}")
        print(f"tax -- {order.tax}")
        print(f"total -- {order.total_amount}")
        assert order.subtotal == Decimal('650.00')
        assert order.delivery_fee == restaurant.delivery_fee
        #tax = 650 * 0.05 = 32.50
        assert order.tax == Decimal('32.50')

#TODOO
    def test_cancel_pending_order(self,api_client,customer_with_address,menu_items):
        print("=====test16 cancel order=====")
        order_id = self._create_order(api_client,customer_with_address,menu_items)
        response = api_client.post(f'/api/orders/new/{order_id}/cancel/')
        print(f"response -- {response.status_code}")
        assert response.status_code == 200
        order = Order.objects.get(order_number=order_id)
        assert order.status == 'cd'

#TODOO
    def test_assign_driver(self,api_client,customer_with_address,menu_items,driver):
        print("=====test17 assign driver=====")
        order_id = self._create_order(api_client,customer_with_address,menu_items)
        response = api_client.post(
            f'/api/orders/new/{order_id}/assign_driver/',
            {'driver_id':str(driver.id)},
            format='json'
        )
        print(f"response -- {response.status_code}")
        print(response.data)
        assert response.status_code == 200
        #driver should be busy now
        dp = DriverProfile.objects.get(user=driver)
        assert dp.is_available == False

#===============================================================================
# 5. REVIEW TESTS
#===============================================================================

@pytest.mark.django_db
class TestReviews:
#TODOO
    def test_review_only_delivered_orders(self,api_client,customer_with_address,menu_items,restaurant):
        print("=====test18 review on non-delivered=====")
        api_client.force_authenticate(user=customer_with_address)
        #create order (its pending not delivered)
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[0].id,'quantity':2},format='json')
        api_client.post('/api/orders/cart/addtocart/',{'menu_item':menu_items[1].id,'quantity':1},format='json')
        resp = api_client.post('/api/orders/cart/checkout/',{'confirm':True},format='json')
        order_id = resp.data['order']['order_number']
        #try to review pending order
        review_data = {
            'order':order_id,
            'restaurant':restaurant.id,
            'rating':5,
            'comment':'great food!'
        }
        response = api_client.post('/api/orders/reviews/',review_data,format='json')
        print(f"response -- {response.status_code}")
        assert response.status_code == 400


#===============================================================================
# 6. Websocket TESTS
#===============================================================================


def get_communicator(consumer_class,path,user):

    communicator = WebsocketCommunicator(consumer_class.as_asgi(),path)
    communicator.scope['user'] = user
    communicator.scope['url_route'] = {'kwargs': {}}

    print(communicator)
    print(communicator.scope['url_route'])
    # /ws/customer/uid/ -> uid
    parts = path.strip('/').split('/')
    if 'customer' in path and len(parts) >= 3:
        #ws/customer/<uuid:user_id>/
        communicator.scope['url_route']['kwargs']['user_id'] = parts[2]
        print("problem here :--")
        print(communicator.scope['url_route']['kwargs']['user_id'])
        print(parts[2])
    elif 'restaurant' in path and len(parts) >= 4:
        #ws/restaurant/orders/<uuid:resto_id>/
        communicator.scope['url_route']['kwargs']['resto_id'] = parts[3]
    elif 'orders' in path and len(parts) >= 3:
        #ws/orders/<uuid:order_id>/
        communicator.scope['url_route']['kwargs']['order_id'] = parts[2]
    elif 'driver' in path:
        #ws/driver/neworders/
        pass #driver has no kwargs

    return communicator


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestCustomerConsumer:
#DONE
    async def test_customer_connects(self,customer):
        print("=====ws test1 customer connect=====")
        user = customer 
        print(user.id)
        comm = get_communicator(CustomerConsumer,f'/ws/customer/{user.id}/',user)
        connected,_ = await comm.connect()
        print(f"connected -- {connected}")
        assert connected == True
        await comm.disconnect()


# #DONE
    async def test_customer_gets_group_notification(self,customer):
        print("=====ws test3 customer group noti=====")
        user = customer
        roomn = f"customer_{user.id}"
        comm = get_communicator(CustomerConsumer,f'/ws/customer/{user.id}/',user)
        connected,_ = await comm.connect()
        assert connected == True

        #simulating the signal - group_send to customer_<id>
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            roomn,
            {
                'type':'chat.message',
                'message':'Your order has been placed',
            }
        )
        response = await comm.receive_json_from(timeout=3)
        print(f"notification recieved -- {response}")
        assert response['message'] == 'Your order has been placed'
        await comm.disconnect()


# #===============================================================================
# # 2. RESTAURANT CONSUMER TESTS
# #===============================================================================

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestRestoConsumer:
#DONE
    async def test_resto_connects(self,resto_owner):
        print("=====ws test4 resto connect=====")
        user = resto_owner
        comm = get_communicator(RestoConsumer,f'/ws/restaurant/orders/{user.id}/',user)
        connected,_ = await comm.connect()
        print(f"connected -- {connected}")
        assert connected == True
        await comm.disconnect()

#DONE
    async def test_resto_gets_new_order_noti(self,resto_owner):
        print("=====ws test5 resto new order=====")
        user = resto_owner
        roomn = f"restaurant_{user.id}"
        comm = get_communicator(RestoConsumer,f'/ws/restaurant/orders/{user.id}/',user)
        connected,_ = await comm.connect()
        assert connected == True

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            roomn,
            {
                'type':'chat.message',
                'message':'New Order for 499.00',
            }
        )
        response = await comm.receive_json_from(timeout=3)
        print(f"resto got -- {response}")
        assert response['message'] == 'New Order for 499.00'
        await comm.disconnect()


# #===============================================================================
# # 3. DRIVER CONSUMER TESTS
# #===============================================================================

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestDriverConsumer:
#DONE
    async def test_driver_connects(self,driver):
        print("=====ws test6 driver connect=====")
        user = driver
        comm = get_communicator(DriverConsumer,f'/ws/driver/neworders/',user)
        connected,_ = await comm.connect()
        print(f"connected -- {connected}")
        assert connected == True
        await comm.disconnect()

#DONE
    async def test_driver_gets_delivery_broadcast(self,driver):
        print("=====ws test7 driver broadcast=====")
        user = driver
        comm = get_communicator(DriverConsumer,'/ws/driver/neworders/',user)
        connected,_ = await comm.connect()
        assert connected == True

        # all drivers get it
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'drivers',
            {
                'type':'chat.message',
                'message':'New Delivery uuid for amount 350.00',
            }
        )
        response = await comm.receive_json_from(timeout=3)
        print(f"driver got -- {response}")
        assert 'New Delivery' in response['message']
        await comm.disconnect()


# #===============================================================================
# # 4. ORDER CONSUMER TESTS (notification app)
# #===============================================================================

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestOrderConsumer:
#DONE
    async def test_order_room_connects(self,customer):
        print("=====ws test8 order room connect=====")
        user = customer
        comm = get_communicator(OrderConsumer,f'/ws/orders/order-000/',user)
        connected,_ = await comm.connect()
        print(f"connected -- {connected}")
        assert connected == True
        await comm.disconnect()

#DONE
    async def test_order_room_gets_status_update(self,customer):
        print("=====ws test9 order status update=====")
        user = customer
        comm = get_communicator(OrderConsumer,'/ws/orders/order-777/',user)
        connected,_ = await comm.connect()
        assert connected == True

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'order_order-777',
            {
                'type':'chat.message',
                'message':'status updated ORD-777: pd -> co',
            }
        )
        response = await comm.receive_json_from(timeout=3)
        print(f"order update -- {response}")
        assert 'pd -> co' in response['message']
        await comm.disconnect()





# #===============================================================================
# # 6. SIGNAL -> WEBSOCKET INTEGRATION
# #===============================================================================

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestSignalToWebsocket:
#DONE
    async def test_signal_sends_to_customer(self,customer):
        print("=====ws test13 signal->customer=====")
        user = customer
        comm = get_communicator(CustomerConsumer,f'/ws/customer/{user.id}/',user)
        connected,_ = await comm.connect()
        assert connected == True

        #this is what user/signals.py send_noti_user does
        
        await sync_to_async(send_noti_user)(
            message='Your Order has been placed',
            orderid=user.id,
            room='customer',
        )

        response = await comm.receive_json_from(timeout=3)
        print(f"customer got signal -- {response}")
        assert response['message'] == 'Your Order has been placed'
        await comm.disconnect()

#DONE
    async def test_signal_sends_to_restaurant(self,resto_owner):
        print("=====ws test14 signal->resto=====")
        user = resto_owner
        comm = get_communicator(RestoConsumer,f'/ws/restaurant/orders/{user.id}/',user)
        connected,_ = await comm.connect()
        assert connected == True

        from user.signals import send_noti_user
        await sync_to_async(send_noti_user)(
            message='New Order for 750.00',
            orderid=user.id,
            room='restaurant',
        )

        response = await comm.receive_json_from(timeout=3)
        print(f"resto got signal -- {response}")
        assert response['message'] == 'New Order for 750.00'
        await comm.disconnect()

#DONE
    async def test_signal_broadcasts_to_drivers(self,driver):
        print("=====ws test15 signal->drivers=====")
        user = driver
        comm = get_communicator(DriverConsumer,'/ws/driver/neworders/',user)
        connected,_ = await comm.connect()
        assert connected == True

        from user.signals import send_noti_user
        await sync_to_async(send_noti_user)(
            message='New Delivery o2msoxm for amount 500',
            orderid='drv1',
            room='driver',
        )

        response = await comm.receive_json_from(timeout=3)
        print(f"driver got signal -- {response}")
        assert 'New Delivery' in response['message']
        await comm.disconnect()

