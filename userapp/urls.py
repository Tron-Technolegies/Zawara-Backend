from django.urls import path
from userapp import views

urlpatterns = [
    path("signup/", views.signup, name='signup'),
    path("login/", views.login, name='login'),
    path("forgot-password/",views.forgot_password, name='forgot_password'),
    path("reset-password/",views.reset_password, name='reset_password'),
    path('view_categories/', views.view_categories, name='view_categories'),
    path("view_products/", views.view_products, name='view_products'),
    path("view_single_product/<int:product_id>/", views.view_single_product, name='view_single_product'),
    path("add_to_cart/",views.add_to_cart,name="add_to_cart"),
    path("view_cart/",views.view_cart,name="view_cart"),
    path("remove_cart_item/<int:item_id>/",views.remove_cart_item,name="remove_cart_item"),
    path("add_to_wishlist/",views.add_to_wishlist),
    path("view_wishlist/",views.view_wishlist),
    path("remove_wishlist_item/<int:wishlist_id>/",views.remove_wishlist_item)
]