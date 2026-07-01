from django.urls import path
from adminapp import views


urlpatterns = [

    path("login/",views.admin_login),

    path('dashboard/', views.dashboard, name='dashboard'),

    path("customers/",views.view_customers,name="view_customers"),
    path("customers/<int:customer_id>/delete/",views.delete_customer,name="view_customers"),

    path('categories/add/', views.add_category, name='add_category'),
    path('categories/', views.view_categories, name='view_categories'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('categories/update/<int:category_id>/', views.update_category, name='update_category'),

    path('product/add/', views.add_product, name='add_product'),
    path('product/', views.view_products, name='view_products'),
    path('product/<int:product_id>/', views.view_product, name='view_product'),
    path('product/update/<int:product_id>/', views.update_product, name='update_product'),
    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),

    path('coupon/create/', views.create_coupon, name='create_coupon'),
    path('coupons/view/', views.view_coupons, name='view_coupon'),
    # path("coupon/view/<int:coupon_id>/", views.view_coupon, name="view_coupon"),
    path("coupon/update/<int:coupon_id>/", views.update_coupon, name="view_coupon"),
    path("coupon/delete/<int:coupon_id>/", views.delete_coupon, name="delete_coupon"),
]