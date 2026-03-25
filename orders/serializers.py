from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from catalog.models import Product
from orders.models import Order, OrderItem


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderItemOutputSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "quantity", "price")


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        items_data = validated_data["items"]
        quantities: dict[int, int] = defaultdict(int)
        for row in items_data:
            p = row["product"]
            quantities[p.pk] += row["quantity"]

        total = Decimal("0")
        order = Order.objects.create(user=user, total=0)

        for product_id, quantity in quantities.items():
            product_locked = Product.objects.select_for_update().get(pk=product_id)
            if product_locked.stock < quantity:
                raise serializers.ValidationError(
                    {"items": f"Insufficient stock for '{product_locked.name}'."}
                )
            line_total = product_locked.price * quantity
            total += line_total
            OrderItem.objects.create(
                order=order,
                product=product_locked,
                quantity=quantity,
                price=product_locked.price,
            )
            product_locked.stock -= quantity
            product_locked.save(update_fields=["stock"])

        order.total = total
        order.save(update_fields=["total"])
        return order


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("id", "status", "total", "created_at", "items")
