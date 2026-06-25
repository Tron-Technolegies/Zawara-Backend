from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import APIView, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
import re
from .models import UserProfile,Cart, CartItem
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


@require_http_methods(["GET"])
def view_categories(request):
    search = request.GET.get("search", "")

    categories = Category.objects.filter(
        Q(name__icontains=search))

    data = [
        {
            "id": category.id,
            "name": category.name,
            "image": category.image.url if category.image else None,
        }
        for category in categories
    ]

    return JsonResponse({"categories": data}, status=200)



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
    

@csrf_exempt
def add_to_cart(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "POST method required"},
            status=405
        )

    try:
        data = json.loads(request.body)

        user = request.user

        product_id = data.get("product_id")
        size = data.get("size")
        quantity = int(
            data.get("quantity", 1)
        )

        product = Product.objects.get(
            id=product_id
        )

        cart, created = Cart.objects.get_or_create(
            user=user
        )

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={
                "quantity": quantity
            }
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return JsonResponse({
            "message": "Product added to cart"
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
    
@csrf_exempt
def view_cart(request):
    try:
        cart = Cart.objects.get(
            user=request.user
        )

        items = []

        for item in cart.items.all():
            items.append({
                "id": item.id,
                "product_id": item.product.id,
                "name": item.product.name,
                "price": str(item.product.price),
                "image": (
                    item.product.image.url
                    if item.product.image
                    else None
                ),
                "size": item.size,
                "quantity": item.quantity,
                "total": float(
                    item.product.price
                ) * item.quantity
            })

        return JsonResponse({
            "items": items
        })

    except Cart.DoesNotExist:
        return JsonResponse({
            "items": []
        })
    
@csrf_exempt
def remove_cart_item(request, item_id):
    try:
        item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )

        item.delete()

        return JsonResponse({
            "message": "Item removed"
        })

    except CartItem.DoesNotExist:
        return JsonResponse(
            {"error": "Item not found"},
            status=404
        )