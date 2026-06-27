from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import APIView, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
import re
from .models import UserProfile,Cart, CartItem,Wishlist
from adminapp.models import Category,Product
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.conf import settings

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Address
from .serializers import AddressSerializer
from rest_framework import status




# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    full_name = request.data.get("full_name")
    email = request.data.get("email")
    password = request.data.get("password")
    mobile=request.data.get("mobile")

    if not re.match(r'^[6-9]\d{9}$', mobile):
        return Response(
        {"error": "Invalid mobile number"},
        status=400
    )

    if not re.match(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
        password
    ):
        return Response(
            {"error": "Password does not meet requirements"},
            status=400
        )

    if not full_name or not email or not password:
        return Response({"error": "full_name, email, password required"}, status=400)

    if User.objects.filter(username=email).exists():
        return Response({"error": "Email already registered"}, status=400)

    parts = full_name.strip().split(" ")
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    UserProfile.objects.create(
        user=user,
        mobile=mobile
    )

    tokens = get_tokens_for_user(user)

    return Response({
        "message": "User created",
        "user_id": user.id,
        "email": user.email,
        "full_name": full_name,
        "mobile" : mobile,
        "tokens": tokens
    }, status=201)



@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)

    tokens = get_tokens_for_user(user)
    full_name = f"{user.first_name} {user.last_name}".strip()

    return Response({
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
        "full_name": full_name,
        "tokens": tokens
    })

@require_http_methods(["GET"])
def view_categories(request):
    search = request.GET.get("search", "")

    categories = Category.objects.filter(
        Q(name__icontains=search)
    ).order_by("priority")

    data = [
        {
            "id": category.id,
            "name": category.name,
            "image": category.image.url if category.image else None,
        }
        for category in categories
    ]

    return JsonResponse({"categories": data}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    print("FORGOT PASSWORD API HIT")
    email = request.data.get("email")
    print("EMAIL:", email)

    if not email:
        return Response(
            {"error": "Email is required"},
            status=400
        )

    user = User.objects.filter(email=email).first()
    print("USER:", user)

    if not user:
        return Response(
            {"message": "If the email exists, a reset link has been sent"}
        )
    print("USER FOUND")

    uid = urlsafe_base64_encode(
        force_bytes(user.pk)
    )

    token = default_token_generator.make_token(
        user
    )

    reset_link = (
        f"http://localhost:5173/resetpassword/"
        f"{uid}/{token}/"
    )

    print("UID:", uid)
    print("TOKEN:", token)
    print("RESET LINK:", reset_link)

    send_mail(
        subject="Reset Your Password",
        message=f"""
Click the link below to reset your password:

{reset_link}

If you did not request this, ignore this email.
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return Response({
        "message": "Password reset link sent"
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    uid = request.data.get("uid")
    token = request.data.get("token")
    password = request.data.get("password")

    if not uid or not token or not password:
        return Response(
            {"error": "uid, token and password required"},
            status=400
        )

    try:
        user_id = urlsafe_base64_decode(
            uid
        ).decode()

        user = User.objects.get(
            pk=user_id
        )

    except Exception:
        return Response(
            {"error": "Invalid reset link"},
            status=400
        )

    if not default_token_generator.check_token(
        user,
        token
    ):
        return Response(
            {"error": "Invalid or expired token"},
            status=400
        )

    user.set_password(password)
    user.save()

    return Response({
        "message": "Password updated successfully"
    })



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_details(request):
    try:
        profile = UserProfile.objects.get(user=request.user)

        return Response({
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "mobile": profile.mobile,
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        return Response(
            {"error": "User profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        return Response(
            {"error": "Profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    user.first_name = request.data.get("first_name", user.first_name)
    user.last_name = request.data.get("last_name", user.last_name)
    user.email = request.data.get("email", user.email)
    user.username = user.email  # Keep username and email in sync

    profile.mobile = request.data.get("mobile", profile.mobile)

    user.save()
    profile.save()

    return Response({
        "message": "Profile updated successfully",
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "mobile": profile.mobile,
    })


@require_http_methods(["GET"])
def view_categories(request):
    search = request.GET.get("search", "")

    categories = Category.objects.filter(
        status="Active"
    )

    if search:
        categories = categories.filter(
            name__icontains=search
        )

    categories = categories.order_by("name")

    data = [
        {
            "id": category.id,
            "name": category.name,
            "image": category.image.url if category.image else None,
        }
        for category in categories
    ]

    return JsonResponse(
        {"categories": data},
        status=200
    )



@csrf_exempt
@require_http_methods(["GET"])
def view_products(request):
    search = request.GET.get("search")
    category = request.GET.get("category")
    gender = request.GET.get("gender")

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 12))
    except ValueError:
        return JsonResponse(
            {"error": "Invalid pagination values"},
            status=400
        )

    offset = (page - 1) * limit

    products = Product.objects.select_related(
        "category"
    ).all()

    if category:
        products = products.filter(category_id=category)

    if gender:
        products = products.filter(gender=gender)

    if search:
        products = products.filter(
            Q(name__icontains=search)
        )

    total_products = products.count()
    total_pages = (total_products + limit - 1) // limit

    products = products[offset:offset + limit]

    data = []

    for product in products:
        data.append({
            "id": product.id,
            "name": product.name,

            "category": {
                "id": product.category.id,
                "name": product.category.name,
            } if product.category else None,

            "gender": product.gender,
            "price": str(product.price),
            "description": product.description,
            "stock": product.stock,
            "image": product.image.url if product.image else None,
        })

    return JsonResponse({
        "page": page,
        "limit": limit,
        "total_products": total_products,
        "total_pages": total_pages,
        "products": data
    }, status=200)


@csrf_exempt
@require_http_methods(["GET"])
def view_single_product(request, product_id):
    try:
        product = Product.objects.select_related(
            "category"
        ).get(id=product_id)

        data = {
            "id": product.id,
            "name": product.name,

            "category": {
                "id": product.category.id,
                "name": product.category.name
            } if product.category else None,

            "gender": product.gender,
            "price": str(product.price),
            "description": product.description,
            "stock": product.stock,

            "image": (
                product.image.url
                if getattr(product, "image", None)
                else None
            ),
        }

        return JsonResponse(data, status=200)

    except Product.DoesNotExist:
        return JsonResponse(
            {"error": "Product not found"},
            status=404
        )
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    try:
        data = request.data

        user = request.user

        product_id = data.get("product_id")
        size = data.get("size")
        quantity = int(data.get("quantity", 1))

        if quantity <= 0:
            return JsonResponse(
                {"error": "Quantity must be greater than 0"},
                status=400
            )

        product = Product.objects.get(id=product_id)

        if quantity > product.stock:
            return JsonResponse(
                {"error": "Not enough stock"},
                status=400
            )

        cart, created = Cart.objects.get_or_create(user=user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={"quantity": quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity

            if new_quantity > product.stock:
                return JsonResponse(
                    {"error": "Only limited stock available"},
                    status=400
                )

            cart_item.quantity = new_quantity
            cart_item.save()

        return JsonResponse({
            "message": "Product added to cart",
            "quantity": cart_item.quantity
        })

    except Product.DoesNotExist:
        return JsonResponse(
            {"error": "Product not found"},
            status=404
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )
    
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)

        items = []
        subtotal = 0

        for item in cart.items.all():
            total = float(item.product.price) * item.quantity
            subtotal += total

            items.append({
                "id": item.id,
                "product_id": item.product.id,
                "name": item.product.name,
                "price": float(item.product.price),
                "image": (
                    item.product.image.url
                    if item.product.image
                    else None
                ),
                "size": item.size,
                "quantity": item.quantity,
                "total": total,
            })

        return JsonResponse({
            "items": items,
            "subtotal": subtotal,
            "total": subtotal,   # You can later subtract discounts or add shipping
        })

    except Cart.DoesNotExist:
        return JsonResponse({
            "items": [],
            "subtotal": 0,
            "total": 0,
        })
    

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )

        cart_item.delete()

        return JsonResponse({
            "message": "Item removed successfully"
        })

    except CartItem.DoesNotExist:
        return JsonResponse(
            {"error": "Cart item not found"},
            status=404
        )
    


import uuid

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["POST"])
@permission_classes([AllowAny])
def add_to_wishlist(request):

    product_id = request.data.get("product_id")

    if not product_id:
        return Response(
            {"error": "Product ID is required"},
            status=400
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.user.is_authenticated:

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        return Response({
            "message": (
                "Added to wishlist"
                if created
                else "Already in wishlist"
            )
        })

    guest_id = request.headers.get("guest_id")

    if not guest_id:
        guest_id = str(uuid.uuid4())

    wishlist_item, created = Wishlist.objects.get_or_create(
        guest_id=guest_id,
        product=product
    )

    return Response({
        "message": (
            "Added to wishlist"
            if created
            else "Already in wishlist"
        ),
        "guest_id": guest_id
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_wishlist(request):

    wishlist = Wishlist.objects.filter(
        user=request.user
    ).select_related("product")

    items = []

    for item in wishlist:

        items.append({
            "id": item.id,
            "product_id": item.product.id,
            "name": item.product.name,
            "category": item.product.category.name,
            "price": float(item.product.price),
            "image": item.product.image.url if item.product.image else None,
        })

    return JsonResponse({
        "items": items
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_wishlist_item(request, wishlist_id):

    try:

        item = Wishlist.objects.get(
            id=wishlist_id,
            user=request.user
        )

        item.delete()

        return JsonResponse({
            "message": "Removed from wishlist"
        })

    except Wishlist.DoesNotExist:

        return JsonResponse(
            {"error": "Wishlist item not found"},
            status=404
        )
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_address(request):

    data = request.data.copy()

    if data.get("is_default"):
        Address.objects.filter(user=request.user).update(is_default=False)

    serializer = AddressSerializer(data=data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_addresses(request):

    addresses = Address.objects.filter(user=request.user)

    serializer = AddressSerializer(addresses, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_default_address(request):

    address = Address.objects.filter(
        user=request.user,
        is_default=True
    ).first()

    if not address:
        return Response(
            {"message": "No default address found."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AddressSerializer(address)

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_address(request, pk):

    try:
        address = Address.objects.get(
            id=pk,
            user=request.user
        )
    except Address.DoesNotExist:
        return Response(
            {"error": "Address not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    data = request.data.copy()

    if data.get("is_default"):
        Address.objects.filter(user=request.user).exclude(id=pk).update(is_default=False)

    serializer = AddressSerializer(
        address,
        data=data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_address(request, pk):

    try:
        address = Address.objects.get(
            id=pk,
            user=request.user
        )
    except Address.DoesNotExist:
        return Response(
            {"error": "Address not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    address.delete()

    return Response(
        {"message": "Address deleted successfully."},
        status=status.HTTP_204_NO_CONTENT
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def set_default_address(request, pk):

    try:
        address = Address.objects.get(
            id=pk,
            user=request.user
        )
    except Address.DoesNotExist:
        return Response(
            {"error": "Address not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    Address.objects.filter(user=request.user).update(is_default=False)

    address.is_default = True
    address.save()

    return Response({"message": "Default address updated successfully."})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):

    orders = (
        Order.objects
        .prefetch_related("items__product")
        .filter(user=request.user)
        .order_by("-created_at")
    )

    order_list = []

    for order in orders:

        products = []

        for item in order.items.all():

            status = order.status.upper()

            if status == "DELIVERED":
                color = "bg-green-500"
            elif status in ["SHIPPED", "IN TRANSIT", "PROCESSING"]:
                color = "bg-blue-500"
            elif status in ["RETURNED", "RETURNED & REFUNDED"]:
                color = "bg-gray-400"
            else:
                color = "bg-yellow-500"

            products.append({
                "image": item.product.image.url if item.product.image else "",
                "name": item.product.name,
                "size": item.size if hasattr(item, "size") else "",
                "qty": item.quantity,
                "price":item.price,
                "status": order.status.upper(),
                "color": color,
            })

        order_list.append({
            "id": order.id,
            "orderNumber": f"#RK-{order.id:06d}",
            "orderDate": order.created_at.strftime("%b %d, %Y"),
            "totalAmount": convert_price(
                order.total_amount,
                order.currency
            ),
            "products": products,
        })

    return Response(order_list)