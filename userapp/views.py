from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import APIView, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
import re
from .models import UserProfile,Cart, CartItem,Wishlist
from adminapp.models import Category,Product,Order,OrderItem,Coupon
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
from .razorpay_client import client
from django.utils import timezone




# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

def calculate_cart_total(cart):
    total = 0
    if cart.exists():
        for item in cart.first().items.all():
            total += item.product.price * item.quantity
    return total


from adminapp.utils import create_admin_notification

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

    # ✅ ADMIN NOTIFICATION (ADD THIS)
    create_admin_notification(
        title="New User Signup",
        message=f"{full_name} has registered with email {email}."
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

    frontend_url = settings.FRONTEND_URL

    reset_link = (
        f"{frontend_url}/resetpassword/{uid}/{token}/"
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




@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response(
            {"error": "Both old and new passwords are required"},
            status=400
        )

    user = request.user

    if not user.check_password(old_password):
        return Response(
            {"error": "Current password is incorrect"},
            status=400
        )

    user.set_password(new_password)
    user.save()

    return Response({
        "message": "Password changed successfully"
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
    name = request.GET.get("name")
    category = request.GET.get("category")
    gender = request.GET.get("gender")
    size = request.GET.get("size")
    material = request.GET.get("material")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    price = request.GET.get("price")
    featured = request.GET.get("featured")
    sections = request.GET.get("sections")

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


    if featured is not None:
        featured = featured.lower() == "true"
        products = products.filter(is_featured=featured)

    if category:
        if category.isdigit():
            products = products.filter(category_id=category)
        else:
            products = products.filter(category__name__icontains=category)

    if gender:
        products = products.filter(gender=gender)

    if sections:
        SECTION_MAP = {
            "none": "none",
            "curated_red_velvet": "curated_red_velvet",
            "red velvet": "curated_red_velvet",

            "curated_chanderi_silks": "curated_chanderi_silks",
            "chanderi silks": "curated_chanderi_silks",

            "summer_chronicles": "summer_chronicles",
            "summer chronicles": "summer_chronicles",

            "heritage_blooms": "heritage_blooms",
            "heritage blooms": "heritage_blooms",
        }

        section_list = [
            s.strip().lower()
            for s in sections.split(",")
            if s.strip()
        ]

        mapped_sections = [
            SECTION_MAP.get(s, s)
            for s in section_list
        ]

        if len(mapped_sections) == 1:
            products = products.filter(
                sections__iexact=mapped_sections[0]
            )
        else:
            products = products.filter(
                sections__in=mapped_sections
            )


    if search:
        products = products.filter(
            Q(name__icontains=search)
        )

    if name:
        products = products.filter(
            Q(name__icontains=name)
        )

    if size:
        SIZE_MAP = {
            "s": "S",
            "small": "S",
            "m": "M",
            "medium": "M",
            "xl": "XL",
            "extra large": "XL",
            "l": "L",
            "large": "L",
        }
        sizes = [s.strip().lower() for s in size.split(",") if s.strip()]
        mapped_sizes = [SIZE_MAP.get(s, s.upper()) for s in sizes]
        if len(mapped_sizes) == 1:
            products = products.filter(size__iexact=mapped_sizes[0])
        elif len(mapped_sizes) > 1:
            products = products.filter(size__in=mapped_sizes)

    if material:
        materials = [m.strip() for m in material.split(",") if m.strip()]
        if len(materials) == 1:
            products = products.filter(material__icontains=materials[0])
        elif len(materials) > 1:
            q_objects = Q()
            for mat in materials:
                q_objects |= Q(material__icontains=mat)
            products = products.filter(q_objects)

    if price:
        try:
            products = products.filter(price=float(price))
        except ValueError:
            pass

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass

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
            "size": product.size,
            "material": product.material,
            "image": product.image.url if product.image else None,
            "sections": product.sections,
            "is_featured": product.is_featured
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
            "size": product.size,
            "material": product.material,

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
    
@csrf_exempt
@require_http_methods(["GET"])
def latest_products(request):
    try:
        limit = int(request.GET.get("limit", 4))
    except ValueError:
        limit = 4

    products = (
        Product.objects.select_related("category")
        .order_by("-id")[:limit]
    )

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
            "size": product.size,
            "material": product.material,
            "image": product.image.url if product.image else None,
        })

    return JsonResponse({
        "products": data
    }, status=200)




@csrf_exempt
@require_http_methods(["GET"])
def latest_featured_products(request):
    try:
        limit = int(request.GET.get("limit", 4))
    except ValueError:
        limit = 4

    products = (
        Product.objects.select_related("category")
        .filter(is_featured=True)
        .order_by("-id")[:limit]
    )

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
            "size": product.size,
            "material": product.material,
            "image": product.image.url if product.image else None,
            "is_featured": product.is_featured,
        })

    return JsonResponse({
        "products": data
    }, status=200)


from decimal import Decimal

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def checkout_summary(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return Response(
            {"error": "Cart is empty"},
            status=status.HTTP_404_NOT_FOUND
        )

    items = []
    subtotal = Decimal("0.00")

    for item in cart.items.select_related("product").all():

        line_total = item.product.price * item.quantity
        subtotal += line_total

        items.append({
            "id": item.id,
            "image": request.build_absolute_uri(
                item.product.image.url
            ) if item.product.image else "",
            "name": item.product.name,
            "size": item.size,
            "quantity": item.quantity,
            "price": str(item.product.price),
            "total": str(line_total),
        })

    shipping = Decimal("0.00")

    total = subtotal + shipping

    return Response({
        "items": items,
        "subtotal": str(subtotal),
        "shipping": str(shipping),
        "total": str(total),
    })

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
    


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_quantity(request, item_id):
    try:
        item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )

        quantity = int(request.data.get("quantity", 1))

        if quantity < 1:
            return Response(
                {"error": "Quantity must be at least 1"},
                status=400
            )

        item.quantity = quantity
        item.save()

        return Response({
            "message": "Quantity updated",
            "quantity": item.quantity
        })

    except CartItem.DoesNotExist:
        return Response(
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
            "category": item.product.category.name if item.product.category else "Uncategorized",
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


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def my_orders(request):
#     orders = (
#         Order.objects
#         .prefetch_related("items__product")
#         .filter(user=request.user)
#         .order_by("-created_at")
#     )

#     order_list = []

#     for order in orders:
#         products = []

#         for item in order.items.all():
#             status = order.status.upper()

#             if status == "COMPLETED":
#                 color = "bg-green-500"
#             elif status in ["SHIPPED", "PROCESSING"]:
#                 color = "bg-blue-500"
#             elif status == "CANCELLED":
#                 color = "bg-red-500"
#             else:
#                 color = "bg-yellow-500"

#             products.append({
#                 "image": request.build_absolute_uri(item.product.image.url) if item.product and item.product.image else "",
#                 "name": item.product.name if item.product else "Unknown Product",
#                 "size": item.size or "",
#                 "qty": item.quantity,
#                 "price": f"₹ {item.price}",
#                 "status": order.get_status_display(),
#                 "color": color,
#             })

#         order_list.append({
#             "id": order.id,
#             "orderNumber": f"#RK-{order.id:06d}",
#             "orderDate": order.created_at.strftime("%b %d, %Y"),
#             "totalAmount": f"₹ {order.total_amount}",
#             "products": products,
#         })

#     return Response({"orders": order_list})

from decimal import Decimal
import razorpay

from django.conf import settings
from django.db import transaction

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from adminapp.models import Order, OrderItem
from userapp.models import Cart, CartItem
from userapp.razorpay_client import get_razorpay_client


# --------------------------------------------------
# Helper: calculate cart total
# --------------------------------------------------
def calculate_cart_total(cart_items):
    total = Decimal("0.00")

    for item in cart_items:
        if not item.product:
            continue

        product_price = item.product.price
        total += Decimal(str(product_price)) * item.quantity

    return total


# --------------------------------------------------
# GET ORDERS
# --------------------------------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders(request):
    try:
        user = request.user
        orders = (
            Order.objects.filter(user=user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

        orders_data = []

        for order in orders:
            products_data = []

            for item in order.items.all():
                image_url = None
                if item.product and getattr(item.product, "image", None):
                    try:
                        image_url = item.product.image.url
                    except Exception:
                        image_url = None

                product_data = {
                    "image": image_url,
                    "name": item.product.name if item.product else "Unknown Product",
                    "size": item.size,
                    "qty": item.quantity,
                    "color": "bg-black",
                    "status": order.get_status_display(),
                    "price": f"₹ {item.price}",
                }
                products_data.append(product_data)

            orders_data.append({
                "id": order.id,
                "orderNumber": f"#ORD{order.id:04d}",
                "orderDate": order.created_at.strftime("%B %d, %Y"),
                "totalAmount": f"₹ {order.total_amount}",
                "products": products_data,
            })

        return Response({"orders": orders_data}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# --------------------------------------------------
# CREATE RAZORPAY ORDER
# --------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    try:
        user = request.user

        # get cart
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            return Response({"error": "Cart not found."}, status=400)

        # get cart items
        cart_items = CartItem.objects.filter(cart=cart).select_related("product")
        if not cart_items.exists():
            return Response({"error": "Cart is empty."}, status=400)

        subtotal = calculate_cart_total(cart_items)

        coupon_code = (request.data.get("coupon_code") or "").strip()
        discount_amount = Decimal("0.00")

        # -------------------------------
        # Add coupon logic here if needed
        # Example:
        # if coupon_code == "SAVE100":
        #     discount_amount = Decimal("100.00")
        # -------------------------------

        final_total = subtotal - discount_amount
        if final_total < 0:
            final_total = Decimal("0.00")

        razorpay_client = get_razorpay_client()
        payment = razorpay_client.order.create({
            "amount": int(final_total * 100),   # rupees to paise
            "currency": "INR",
            "payment_capture": 1,
        })

        return Response({
            "key": settings.RAZORPAY_KEY_ID,
            "order_id": payment["id"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "subtotal": str(subtotal),
            "discount_amount": str(discount_amount),
            "coupon_code": coupon_code,
            "final_total": str(final_total),
        }, status=200)

    except razorpay.errors.BadRequestError as e:
        return Response(
            {
                "error": "Razorpay authentication failed. Check your API keys.",
                "detail": str(e),
            },
            status=500,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# --------------------------------------------------
# VERIFY PAYMENT + CREATE ORDER
# --------------------------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    razorpay_order_id = request.data.get("razorpay_order_id")
    razorpay_payment_id = request.data.get("razorpay_payment_id")
    razorpay_signature = request.data.get("razorpay_signature")

    email = request.data.get("email") or request.user.email or "test@example.com"
    phone = request.data.get("phone") or "null"
    shipping_address = request.data.get("shipping_address") or "Address not provided"

    coupon_code = (request.data.get("coupon_code") or "").strip()
    discount_amount = Decimal(str(request.data.get("discount_amount", 0) or 0))

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return Response({
            "success": False,
            "message": "Missing Razorpay payment details."
        }, status=400)

    try:
        # Verify Razorpay signature
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        razorpay_client = get_razorpay_client()
        razorpay_client.utility.verify_payment_signature(params_dict)

        user = request.user

        # get cart
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            return Response({
                "success": False,
                "message": "Cart not found."
            }, status=400)

        # get cart items
        cart_items = CartItem.objects.filter(cart=cart).select_related("product")
        if not cart_items.exists():
            return Response({
                "success": False,
                "message": "Cart is empty."
            }, status=400)

        # Prevent duplicate order creation
        existing_order = Order.objects.filter(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id
        ).first()

        if existing_order:
            return Response({
                "success": True,
                "message": "Order already created.",
                "order_id": existing_order.id
            }, status=200)

        subtotal = Decimal("0.00")
        for item in cart_items:
            if not item.product:
                continue

            product_price = item.product.price
            subtotal += Decimal(str(product_price)) * item.quantity

        total_amount = subtotal - discount_amount
        if total_amount < 0:
            total_amount = Decimal("0.00")

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                email=email,
                phone=phone,
                shipping_address=shipping_address,
                total_amount=total_amount,
                coupon_code=coupon_code if coupon_code else None,
                discount_amount=discount_amount,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                payment_status="paid",
                status="processing",
            )

            for item in cart_items:
                if not item.product:
                    continue

                product_price = item.product.price

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=product_price,
                    size=item.size or "",
                    material=item.product.material or "",
                )

                # stock update
                if item.product.stock is not None:
                    item.product.stock -= item.quantity
                    if item.product.stock < 0:
                        item.product.stock = 0
                    item.product.save()

            # clear cart after successful order creation
            cart_items.delete()

        return Response({
            "success": True,
            "message": "Payment verified and order created successfully.",
            "order_id": order.id
        }, status=200)

    except Exception as e:
        return Response({
            "success": False,
            "message": "Payment verification failed.",
            "error": str(e)
        }, status=400)
    


@csrf_exempt
def apply_coupon(request):

    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body)

    code = data.get("code")
    subtotal = Decimal(str(data.get("subtotal")))

    try:
        coupon = Coupon.objects.get(code=code)

    except Coupon.DoesNotExist:
        return JsonResponse(
            {"error": "Invalid Coupon"},
            status=404
        )

    now = timezone.now()

    if coupon.valid_from > now:
        return JsonResponse(
            {"error": "Coupon not active yet"},
            status=400
        )

    if coupon.valid_to < now:
        return JsonResponse(
            {"error": "Coupon expired"},
            status=400
        )

    if coupon.discount_type == "percentage":

        discount = (
            subtotal *
            coupon.discount_value
        ) / Decimal("100")

    else:

        discount = coupon.discount_value

    total = subtotal - discount

    if total < 0:
        total = 0

    return JsonResponse({

        "coupon": coupon.code,

        "discount": float(discount),

        "subtotal": float(subtotal),

        "total": float(total),

        "message": "Coupon Applied Successfully"

    })


@csrf_exempt
def available_coupons(request):

    now = timezone.now()

    coupons = Coupon.objects.filter(
        valid_from__lte=now,
        valid_to__gte=now
    )

    data = []

    for coupon in coupons:

        data.append({

            "id": coupon.id,
            "name": coupon.name,
            "description": coupon.description,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value)

        })

    return JsonResponse(data, safe=False)


