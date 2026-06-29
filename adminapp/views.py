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
            "is_featured": product.is_featured,
        }, status=201)

    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found"},status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)
    

@require_http_methods(["GET"])
def view_products(request):
    products = Product.objects.select_related("category")

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
            "is_published": True
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
            },
            "gender": product.gender,
            "size": product.size,
            "material": product.material,
            "price": str(product.price),
            "description": product.description,
            "stock": product.stock,
            "image": product.image.url if product.image else None,
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


def dashboard(request):
    try:
        total_products = Product.objects.count()
        total_categories = Category.objects.count()

        return JsonResponse({
            "total_products": total_products,
            "total_categories": total_categories,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)