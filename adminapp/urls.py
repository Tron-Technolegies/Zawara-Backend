from django.urls import path
from adminapp import views


urlpatterns = [
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/', views.view_categories, name='view_categories'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    # path('update_category/<int:category_id>/', views.update_category, name='update_category'),

    path('product/add/', views.add_product, name='add_product'),
    path('product/', views.view_products, name='view_products'),
    path('product/<int:product_id>/', views.view_product, name='view_product'),
    path('product/update/<int:product_id>/', views.update_product, name='update_product'),
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),

]