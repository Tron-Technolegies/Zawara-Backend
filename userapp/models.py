from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from adminapp.models import Product


# Create your models here.
class UserProfile(models.Model):
    user= models.OneToOneField(User, on_delete=models.CASCADE)
    mobile=models.CharField(max_length=15)

    def __str__(self):
        return self.user.username
    

class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )



class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    size = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "cart",
            "product",
            "size"
        )


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name="wishlist")
    guest_id = models.CharField(max_length=100,null=True,blank=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    




