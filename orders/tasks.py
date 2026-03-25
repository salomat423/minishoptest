from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from orders.models import Order


@shared_task
def send_order_confirmation(order_id: int) -> None:
    order = Order.objects.select_related("user").get(pk=order_id)
    user = order.user
    recipient = getattr(user, "email", None) or ""
    if not recipient:
        return
    send_mail(
        subject=f"MiniShop: order #{order_id} received",
        message=(
            f"Thank you for your order.\n\n"
            f"Order #{order_id}\n"
            f"Total: {order.total}\n"
            f"Status: {order.status}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=True,
    )


@shared_task
def update_order_status(order_id: int) -> None:
    order = Order.objects.get(pk=order_id)
    if order.status == Order.Status.PENDING:
        order.status = Order.Status.PROCESSING
        order.save(update_fields=["status"])
