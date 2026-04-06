from rest_framework import serializers
from user.models import *
import logging

logger = logging.getLogger('user')

class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name',read_only=True)
    item_price = serializers.DecimalField(source='menu_item.price',max_digits=8,decimal_places=2,read_only=True)
    item_total = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['menu_item','quantity' #these 2 fields will be from user
                  ,'id','item_name','item_price','item_total'] #automatically fetched
        read_only_fields = ['id']

    def get_item_total(self,obj):
        return obj.menu_item.price * obj.quantity

class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='menu_item.name',read_only=True)
    line_total = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ['id','menu_item','item_name','quantity','uprice','line_total']
        read_only_fields = ['uprice']

    def get_line_total(self,obj):
        return obj.uprice * obj.quantity




class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='item_for',many=True,read_only=True)
    can_cancel = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    final_total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_number','customer','restaurant','driver','status',
                  'delivery_address','adratorder','subtotal','delivery_fee','tax',
                  'total_amount','special_instructions','estimated_delivery_time',
                  'actual_delivery_time','created_at','items',
                   'can_cancel','can_review','items_count','final_total'] 

    def get_can_cancel(self,obj):
        print(f"checking if order {obj.order_number} can be cancelled")
        return obj.is_cancellable

    def get_can_review(self,obj):
        #can review only if delivered and not already reviewed
        if obj.status != 'dl':
            return False
        already = Review.objects.filter(order=obj,customer=obj.customer).exists()
        print(f"can review: {not already}")
        return not already

    def get_items_count(self,obj):
        count = obj.item_for.count()
        print(f"items count: {count}")
        return count

    def get_final_total(self,obj):
        print(f"final total: {obj.total_amount}")
        return str(obj.total_amount)


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.SC)

    def validate_status(self,value):
        order = self.context['order']
        allowed = order.TRANSITIONS.get(order.status,[])
        if value not in allowed:
            raise serializers.ValidationError(
                f"cant change from {order.get_status_display()} to {value}. allowed: {allowed}"
            )
        return value
    
    class Meta:
        model = Order

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    class Meta:
        model = Review
        fields = ['id','customer','customer_name','restaurant','menu_item','order','rating','comment','created_at']
        read_only_fields = ['customer']

    def get_customer_name(self,obj):
        return f"{obj.customer.first_name}"

    def validate_rating(self,value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("rating should be between 1 and 5")
        return value

    def validate(self,data):
        request = self.context['request']
        order = data.get('order')
        logger.info(f"===validating review for order {order.order_number}===")
        if order.status != 'dl':
            raise serializers.ValidationError("you can only review delivered orders")
        if order.customer != request.user:
            raise serializers.ValidationError("you can only review your own orders")
        if Review.objects.filter(customer=request.user,order=order).exists():
            raise serializers.ValidationError("you already reviewed this order")
        return data

    def create(self,validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
