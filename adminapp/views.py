from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from adminapp.models import Category



from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@api_view(["POST"])
def admin_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "Email not found"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.check_password(password):
        return Response(
            {"error": "Wrong password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_staff:
        return Response(
            {"error": "Admin access required"},
            status=status.HTTP_403_FORBIDDEN
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "Admin login successful",
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    })


from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser

@api_view(["GET"])
@permission_classes([AllowAny])
def view_customers(request):
    customers = User.objects.filter(is_staff=False).select_related("userprofile")
    data = []
    for customer in customers:
        data.append({
            "id": customer.id,
            "full_name": f"{customer.first_name} {customer.last_name}".strip(),
            "email": customer.email,
            "mobile": customer.userprofile.mobile if hasattr(customer, "userprofile") else "",
            "date_joined": customer.date_joined,
            "is_active": customer.is_active,
        })

    return Response(data)

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

@api_view(["DELETE"])
@permission_classes([AllowAny])   # Change to AllowAny while testing if needed
def delete_customer(request, customer_id):
    customer = get_object_or_404(User, id=customer_id)

    # Prevent deleting admin accounts
    if customer.is_staff:
        return Response(
            {"error": "Admin users cannot be deleted."},
            status=400
        )

    customer.delete()

    return Response(
        {"message": "Customer deleted successfully."},
        status=200
    )


@csrf_exempt
@require_http_methods(["POST"])
def add_category(request):
    try:
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        status = request.POST.get("status", "Active")
        image = request.FILES.get("image") 

        if not name:
            return JsonResponse(
                {"error": "Category name is required"},
                status=400
            )

        category = Category.objects.create(
            name=name,
            description=description,
            status=status,
            image=image,
        )

        return JsonResponse({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "status": category.status,
            "image": category.image.url if category.image else None,
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    


@require_http_methods(["GET"])
def view_categories(request):
    try:
        categories = Category.objects.all().order_by("id")

        data = [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "status": category.status,
                "image": category.image.url if category.image else None,
            }
            for category in categories
        ]

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
@require_http_methods(["POST"])
def update_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)

        category.name = request.POST.get("name", category.name)
        category.description = request.POST.get("description", category.description)
        category.status = request.POST.get("status", category.status)

        # Update image if a new one is uploaded
        image = request.FILES.get("image")
        if image:
            category.image = image

        category.save()

        return JsonResponse({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "status": category.status,
            "image": category.image.url if category.image else None,
            "message": "Category updated successfully"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        category.delete()

        return JsonResponse({
            "message": "Category deleted successfully",
            "id": category_id
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from adminapp.models import Product


import json

@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        gender = request.POST.get("gender")
        price = request.POST.get("price")
        size = request.POST.get("size")
        material = request.POST.get("material")
        description = request.POST.get("description", "")
        stock = request.POST.get("stock", 0)
        image = request.FILES.get("image")
        sections = request.POST.get("sections", "none")
        is_featured = request.POST.get("is_featured", "false").lower() == "true"

        if not all([name, category_id, gender, size, price]):
            return JsonResponse(
                {"error": "name, category, gender, size and price are required"},
                status=400
            )

        category = Category.objects.get(id=category_id)

        product = Product.objects.create(
            name=name,
            category=category,
            gender=gender,
            price=price,
            size=size,
            material=material,
            description=description,
            stock=stock,
            image=image,
            sections=sections,
            is_featured=is_featured,
        )

        return JsonResponse({
            "id": product.id,
            "name": product.name,
            "category": {
                "id": product.category.id,
                "name": product.category.name
            },
            "gender": product.gender,
            "price": str(product.price),
            "size": product.size,
            "material": product.material,
            "image": product.image.url if product.image else None,
            "description": product.description,
            "stock": product.stock,
            "sections":product.sections,
            "is_featured": product.is_featured,
        }, status=201)

    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found"},status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)
    

@require_http_methods(["GET"])
def view_products(request):
    products = Product.objects.select_related("category").order_by("id")

    data = []

    for product in products:
        data.append({
            "id": product.id,
            "name": product.name,
            "category": {
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None,
            "gender": product.gender,
            "price": str(product.price),
            "size": product.size,
            "material": product.material, 
            "description": product.description,
            "stock": product.stock,
            "image": product.image.url if product.image else None,
            "is_featured": product.is_featured,
            "sections": product.sections,
            # "is_published": True
        })

    return JsonResponse(data, safe=False)

from django.shortcuts import get_object_or_404

@require_http_methods(["GET"])
def view_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)

        return JsonResponse({
            "id": product.id,
            "name": product.name,
            "category": product.category.name if product.category else None,
            "gender": product.gender,
            "price": str(product.price),
            "size": product.size,
            "material": product.material,
            "description": product.description,
            "stock": product.stock,
            "is_featured": product.is_featured,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
        
@csrf_exempt
@require_http_methods(["POST"])
def update_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)

        product.name = request.POST.get("name", product.name)

        category_id = request.POST.get("category")
        if category_id:
            product.category = Category.objects.get(id=category_id)

        product.gender = request.POST.get("gender", product.gender)
        product.size = request.POST.get("size", product.size)
        product.material = request.POST.get("material", product.material)
        product.price = request.POST.get("price", product.price)
        product.description = request.POST.get(
            "description",
            product.description
        )
        product.stock = request.POST.get("stock", product.stock)

        # Featured product
        is_featured = request.POST.get("is_featured")
        if is_featured is not None:
            product.is_featured = is_featured.lower() == "true"

        # Homepage section
        sections = request.POST.get("sections")
        if sections:
            product.sections = sections

        # Image update
        image = request.FILES.get("image")
        if image:
            product.image = image

        product.save()

        return JsonResponse({
            "id": product.id,
            "name": product.name,
            "category": {
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None,
            "gender": product.gender,
            "size": product.size,
            "material": product.material,
            "price": str(product.price),
            "description": product.description,
            "stock": product.stock,
            "image": product.image.url if product.image else None,
            "is_featured": product.is_featured,
            "sections": product.sections,
        })

    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)

        product.delete()

        return JsonResponse({
            "message": "Product deleted successfully"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)

from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category, Order, OrderItem


def dashboard(request):
    try:
        total_products = Product.objects.count()
        total_categories = Category.objects.count()
        total_orders = Order.objects.count()

        # =========================
        # Recent Orders
        # =========================
        recent_orders = []
        orders = Order.objects.all().order_by("-id")[:5]

        for order in orders:
            items = OrderItem.objects.filter(order=order).select_related("product")
            product_names = []

            for item in items:
                if item.product:
                    product_names.append(item.product.name)

            recent_orders.append({
                "order_id": order.id,
                "products": ", ".join(product_names),
                "username": order.user.username if order.user else None,
                "status": order.status,
                "total_amount": str(order.total_amount),
            })

        # =========================
        # Top Sold Products
        # =========================
        top_products_qs = (
            OrderItem.objects
            .filter(product__isnull=False)
            .values("product")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold", "product")[:5]
        )

        top_products = []
        for item in top_products_qs:
            product = Product.objects.filter(id=item["product"]).first()

            if product:
                image_url = None

                if product.image:
                    try:
                        image_url = product.image.url
                    except Exception:
                        image_url = str(product.image)

                top_products.append({
                    "id": product.id,
                    "name": product.name,
                    "image": image_url,
                    "sold": item["total_sold"]
                })

        # =========================
        # Sales Overview - Last 7 Days
        # =========================
        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        last_7_days_orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today
        )

        total_revenue = last_7_days_orders.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        orders_count = last_7_days_orders.count()

        avg_order_value = 0
        if orders_count > 0:
            avg_order_value = round(float(total_revenue) / orders_count, 2)

        refunded_orders = last_7_days_orders.filter(status__iexact="refunded")
        refunds = refunded_orders.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        # =========================
        # Previous 7 Days - for growth %
        # =========================
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date - timedelta(days=1)

        prev_7_days_orders = Order.objects.filter(
            created_at__date__gte=prev_start,
            created_at__date__lte=prev_end
        )

        prev_total_revenue = prev_7_days_orders.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        prev_orders_count = prev_7_days_orders.count()

        prev_avg_order_value = 0
        if prev_orders_count > 0:
            prev_avg_order_value = round(float(prev_total_revenue) / prev_orders_count, 2)

        prev_refunds = prev_7_days_orders.filter(status__iexact="refunded").aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        def calculate_growth(current, previous):
            current = float(current or 0)
            previous = float(previous or 0)

            if previous == 0:
                return 100.0 if current > 0 else 0.0

            return round(((current - previous) / previous) * 100, 1)

        growth_revenue = calculate_growth(total_revenue, prev_total_revenue)
        growth_orders = calculate_growth(orders_count, prev_orders_count)
        growth_avg_order = calculate_growth(avg_order_value, prev_avg_order_value)
        growth_refunds = calculate_growth(refunds, prev_refunds)

        # =========================
        # Chart Data for Last 7 Days
        # =========================
        chart_data = []

        for i in range(7):
            day = start_date + timedelta(days=i)

            day_total = Order.objects.filter(
                created_at__date=day
            ).aggregate(total=Sum("total_amount"))["total"] or 0

            chart_data.append({
                "day": day.strftime("%b %d"),
                "sales": float(day_total)
            })

        sales_overview = {
            "total_revenue": round(float(total_revenue), 2),
            "orders": orders_count,
            "avg_order_value": avg_order_value,
            "refunds": round(float(refunds), 2),
            "growth_revenue": growth_revenue,
            "growth_orders": growth_orders,
            "growth_avg_order": growth_avg_order,
            "growth_refunds": growth_refunds,
            "chart_data": chart_data
        }

        return JsonResponse({
            "total_products": total_products,
            "total_categories": total_categories,
            "total_orders": total_orders,
            "recent_orders": recent_orders,
            "top_products": top_products,
            "sales_overview": sales_overview
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


from .models import Coupon

@csrf_exempt
@require_http_methods(["POST"])
def create_coupon(request):
    data = json.loads(request.body)

    Coupon.objects.create(
        name=data.get("name"),
        description=data.get("description"),
        code=data.get("code"),
        discount_type=data.get("discount_type"),
        discount_value=data.get("discount_value"),
        valid_from=data.get("valid_from"),
        valid_to=data.get("valid_to"),
    )

    return JsonResponse({"message": "Coupon created successfully."}, status=201)


@csrf_exempt
def view_coupons(request):
    coupons = list(Coupon.objects.all().values())
    return JsonResponse(coupons, safe=False)


# @csrf_exempt
# def view_coupon(request, coupon_id):
#     try:
#         coupon = Coupon.objects.values().get(id=coupon_id)
#         return JsonResponse(coupon, status=200)

#     except Coupon.DoesNotExist:
#         return JsonResponse({"error": "Coupon not found."},status=404)


@csrf_exempt
@require_http_methods(["POST"])
def update_coupon(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return JsonResponse({"error": "Coupon not found."},status=404)

    data = json.loads(request.body)

    coupon.name = data.get("name", coupon.name)
    coupon.description = data.get("description", coupon.description)
    coupon.code = data.get("code", coupon.code)
    coupon.discount_type = data.get("discount_type", coupon.discount_type)
    coupon.discount_value = data.get("discount_value", coupon.discount_value)
    coupon.valid_from = data.get("valid_from", coupon.valid_from)
    coupon.valid_to = data.get("valid_to", coupon.valid_to)

    coupon.save()

    return JsonResponse({"message": "Coupon updated successfully."},status=200)



@csrf_exempt
@require_http_methods(["DELETE"])
def delete_coupon(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        coupon.delete()

        return JsonResponse({"message": "Coupon deleted successfully."},status=200)

    except Coupon.DoesNotExist:
        return JsonResponse({"error": "Coupon not found."},status=404)
    


from .models import Notification
from .serializers import NotificationSerializer


@api_view(["GET"])
def admin_notifications(request):
    notifications = Notification.objects.all().order_by("-created_at")
    serializer = NotificationSerializer(notifications, many=True)
    unread_count = notifications.count()   # since unread ones are the ones still موجود

    return Response({
        "notifications": serializer.data,
        "unread_count": unread_count
    })


@api_view(["POST"])
def mark_notification_as_read(request, pk):
    try:
        notification = Notification.objects.get(id=pk)
        # delete notification when admin reads it
        notification.delete()
        unread_count = Notification.objects.count()
        return Response({
            "message": "Notification deleted after reading",
            "unread_count": unread_count
        }, status=200)

    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=404)


@api_view(["POST"])
def mark_all_notifications_as_read(request):
    # delete all notifications instead of marking as read
    Notification.objects.all().delete()

    return Response({
        "message": "All notifications deleted",
        "unread_count": 0
    }, status=200)


from adminapp.models import Order

@api_view(["GET"])
def admin_get_orders(request):
    try:
        orders = (
            Order.objects
            .select_related("user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

        orders_data = []

        for order in orders:
            products_data = []

            for item in order.items.all():
                products_data.append({
                    "name": item.product.name if item.product else "Unknown Product",
                    "qty": item.quantity,
                    "size": item.size if item.size else "",
                })

            orders_data.append({
                "id": order.id,
                "orderNumber": f"#ORD{order.id:04d}",
                "customerId": order.user.id if order.user else None,
                "customerName": order.user.username if order.user else "Guest",
                "customerEmail": order.email,
                "phone": order.phone,
                "shippingAddress": order.shipping_address,
                "orderDate": order.created_at.strftime("%B %d, %Y"),
                "totalAmount": f"₹ {order.total_amount}",
                "paymentStatus": order.payment_status,
                "orderStatus": order.get_status_display(),
                "trackingNumber": order.tracking_number,
                "trackingLink": order.tracking_link,
                "shipmentId": order.shipment_id,
                "razorpayOrderId": order.razorpay_order_id,
                "razorpayPaymentId": order.razorpay_payment_id,
                "products": products_data,
            })

        return Response({"orders": orders_data}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)