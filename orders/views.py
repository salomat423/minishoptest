from django.conf import settings
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from orders.models import Order
from orders.serializers import OrderCreateSerializer, OrderDetailSerializer
from orders.tasks import send_order_confirmation, update_order_status


class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.prefetch_related("items__product").filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        send_order_confirmation.delay(order.id)
        delay_sec = settings.ORDER_PROCESSING_DELAY_MINUTES * 60
        update_order_status.apply_async(args=[order.id], countdown=delay_sec)
        out = OrderDetailSerializer(order, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=201, headers=headers)
