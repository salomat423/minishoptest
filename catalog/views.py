from django.db.models import Q
from rest_framework import permissions, viewsets

from catalog.models import Product
from catalog.serializers import ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.select_related("category").all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search))
        return qs
