from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from adminapp.models import Category


@csrf_exempt
@require_http_methods(["POST"])
def add_category(request):
    try:
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        status = request.POST.get("status", "Active")

        if not name:
            return JsonResponse(
                {"error": "Category name is required"},
                status=400
            )

        category = Category.objects.create(
            name=name,
            description=description,
            status=status
        )

        return JsonResponse({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "status": category.status,
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def view_categories(request):
    try:
        categories = Category.objects.all()

        data = [
            {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "status": category.status,
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
        category = get_object_or_404(Category,id=category_id)
        category.name = request.POST.get("name",category.name)
        category.description = request.POST.get("description",category.description)
        category.status = request.POST.get("status",category.status)
        category.save()

        return JsonResponse({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "status": category.status,
            "message": "Category updated successfully"
        })

    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)


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
        data = json.loads(request.body)

        name = data.get("name")
        category_id = data.get("category")
        gender = data.get("gender")
        price = data.get("price")
        size= data.get("size")
        description = data.get("description", "")
        stock = data.get("stock", 0)

        if not all([name, category_id, gender,size, price]):
            return JsonResponse(
                {"error": "name, category, gender,size and price are required"},
                status=400
            )

        category = Category.objects.get(id=category_id)

        product = Product.objects.create(
            name=name,
            category=category,
            gender=gender,
            price=price,
            size=size,
            description=description,
            stock=stock,
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
            "size":product.size,
            "description": product.description,
            "stock": product.stock,
        }, status=201)

    except Category.DoesNotExist:
        return JsonResponse(
            {"error": "Category not found"},
            status=404
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )



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
            "size":product.size,
            "description": product.description,
            "stock": product.stock,
            "image": None,
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
            "description": product.description,
            "stock": product.stock,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

@csrf_exempt
@require_http_methods(["POST"])
def update_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)

        data = json.loads(request.body)

        product.name = data.get("name", product.name)

        category_id = data.get("category")
        if category_id:
            product.category = Category.objects.get(id=category_id)

        product.gender = data.get("gender", product.gender)
        product.size = data.get("size", product.size)
        product.price = data.get("price", product.price)
        product.description = data.get(
            "description",
            product.description
        )
        product.stock = data.get("stock", product.stock)

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
            "price": str(product.price),
            "description": product.description,
            "stock": product.stock,
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