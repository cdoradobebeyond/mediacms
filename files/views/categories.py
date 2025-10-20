from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from ..methods import is_mediacms_editor
from ..models import Category, CategoryPurchase, Tag
from ..serializers import CategorySerializer, TagSerializer


class CategoryList(APIView):
    """List categories"""

    @swagger_auto_schema(
        manual_parameters=[],
        tags=['Categories'],
        operation_summary='Lists Categories',
        operation_description='Lists all categories',
        responses={
            200: openapi.Response('response description', CategorySerializer),
        },
    )
    def get(self, request, format=None):
        base_filters = {}

        if not is_mediacms_editor(request.user):
            base_filters = {"is_rbac_category": False}

        base_queryset = Category.objects.prefetch_related("user")
        categories = base_queryset.filter(**base_filters)

        if not is_mediacms_editor(request.user):
            if getattr(settings, 'USE_RBAC', False) and request.user.is_authenticated:
                rbac_categories = request.user.get_rbac_categories_as_member()
                categories = categories.union(rbac_categories)

        categories = categories.order_by("title")

        serializer = CategorySerializer(categories, many=True, context={"request": request})
        ret = serializer.data
        return Response(ret)


class TagList(APIView):
    """List tags"""

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(name='page', type=openapi.TYPE_INTEGER, in_=openapi.IN_QUERY, description='Page number'),
        ],
        tags=['Tags'],
        operation_summary='Lists Tags',
        operation_description='Paginated listing of all tags',
        responses={
            200: openapi.Response('response description', TagSerializer),
        },
    )
    def get(self, request, format=None):
        tags = Tag.objects.filter().order_by("-media_count")
        pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
        paginator = pagination_class()
        page = paginator.paginate_queryset(tags, request)
        serializer = TagSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class CategoryPurchaseView(APIView):
    """Registers a purchase that grants access to a category."""

    permission_classes = (permissions.IsAuthenticated,)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='category_uid',
                type=openapi.TYPE_STRING,
                in_=openapi.IN_PATH,
                description='Unique identifier of the category to purchase',
                required=True,
            )
        ],
        tags=['Categories'],
        operation_summary='Purchase category access',
        operation_description='Creates a purchase that grants the authenticated user access to all media in the category',
        responses={200: 'category already unlocked', 201: 'category unlocked', 400: 'bad request'},
    )
    def post(self, request, category_uid, format=None):
        category = get_object_or_404(Category, uid=category_uid)

        if not category.payment_required:
            return Response(
                {"detail": "category does not require payment", "payment_required": False},
                status=status.HTTP_400_BAD_REQUEST,
            )

        purchase, created = CategoryPurchase.objects.get_or_create(
            user=request.user,
            category=category,
            defaults={"amount": category.price, "currency": category.currency},
        )

        if not created and (purchase.amount != category.price or purchase.currency != category.currency):
            purchase.amount = category.price
            purchase.currency = category.currency
            purchase.save(update_fields=["amount", "currency"])

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        detail = "category unlocked" if created else "category already unlocked"

        return Response(
            {
                "detail": detail,
                "purchase_id": purchase.id,
                "payment_required": False,
                "price": format(category.price, ".2f"),
                "currency": category.currency,
                "user_has_access": request.user.has_paid_access_to_category(category),
            },
            status=status_code,
        )
