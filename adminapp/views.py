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
        description = data.get("description", "")
        stock = data.get("stock", 0)

        if not all([name, category_id, gender, price]):
            return JsonResponse(
                {"error": "name, category, gender and price are required"},
                status=400
            )

        category = Category.objects.get(id=category_id)

        product = Product.objects.create(
            name=name,
            category=category,
            gender=gender,
            price=price,
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

        product.name = request.POST.get("name", product.name)

        category_id = request.POST.get("category")
        if category_id:
            product.category = Category.objects.get(id=category_id)

        product.gender = request.POST.get("gender", product.gender)
        product.price = request.POST.get("price", product.price)
        product.description = request.POST.get(
            "description",
            product.description
        )
        product.stock = request.POST.get("stock", product.stock)

        product.save()

        return JsonResponse({"message": "Product updated successfully"})

    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found"},status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)},status=500)
    

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