from django.urls import path
from userapp import views

urlpatterns = [
    path("signup/", views.signup, name='signup'),
    path("login/", views.login, name='login'),
    path("user_details/", views.user_details, name="user_details"),
    path("update-profile/", views.update_profile, name="update_profile"),
    path("checkout-summary/",views.checkout_summary,name="checkout_summary"),

    path("forgot-password/",views.forgot_password, name='forgot_password'),
    path("reset-password/",views.reset_password, name='reset_password'),
    path('view_categories/', views.view_categories, name='view_categories'),
    path("view_products/", views.view_products, name='view_products'),
    path("view_single_product/<int:product_id>/", views.view_single_product, name='view_single_product'),
    path("latest-products/", views.latest_products, name="latest_products"),


    path("add_to_cart/",views.add_to_cart,name="add_to_cart"),
    path("view_cart/",views.view_cart,name="view_cart"),
    path("remove_cart_item/<int:item_id>/",views.remove_cart_item,name="remove_cart_item"),
    path("update_cart_quantity/<int:item_id>/",views.update_cart_quantity,name="update_cart_quantity"),


    path("add_to_wishlist/",views.add_to_wishlist,name="add_to_wishlist"),
    path("view_wishlist/",views.view_wishlist,name="view_wishlist"),
    path("remove_wishlist_item/<int:wishlist_id>/",views.remove_wishlist_item),
    
    path("address/add/", views.add_address,name="address_add"),
    path("address/", views.get_addresses),
    path("address/default/", views.get_default_address),
    path("address/update/<int:pk>/", views.update_address),
    path("address/delete/<int:pk>/", views.delete_address),
    path("address/default/<int:pk>/", views.set_default_address),


    path("create-order/",views.create_order,name="create_order"),
    path("verify-payment/",views.verify_payment,name="verify_payment"),
]