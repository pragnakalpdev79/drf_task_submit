from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from user.models import Order
import json
import logging

logger = logging.getLogger("user")





@receiver(pre_save,sender=Order)
def order_status_notify(sender,instance,**kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if old.status != instance.status:
        print("order status changed!!----------------------")
        logger.info(f"Order {instance.order_number}: {old.status} -> {instance.status}")

