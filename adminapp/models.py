from django.utils import timezone
from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = CloudinaryField("category", blank=True, null=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
        ],
        default="Active"
    )

class Product(models.Model):
    GENDER_CHOICES = (
        ("men", "Men"),
        ("women", "Women"),
    )
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Null')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)
    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L","Large"),
        ("XL", "Extra Large"),
    ]

    SECTION_CHOICES = [
        ("none", "None"),
        ("curated_redvelvet", "Curated - Red Velvet"),
        ("curated_Chanderisilks", "Curated - Chanderi Silks"),
        ("summer_chronicles", "Summer Chronicles"),
        ("heritage_blooms", "Heritage Blooms"),
    ]

    size = models.CharField(max_length=2,choices=SIZE_CHOICES)
    sections = models.CharField(max_length=30,choices=SECTION_CHOICES,default="none",)
    image = CloudinaryField("image", blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    is_featured = models.BooleanField(default=False)

class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(default="test@example.com")
    phone = models.CharField(max_length=20, default='null')
    shipping_address = models.TextField(default='null')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razorpay_order_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=300, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default="pending")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    tracking_link = models.URLField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    shipment_id = models.CharField(max_length=255, blank=True, null=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=50)
    material = models.CharField(max_length=100)

class Coupon(models.Model):
    name = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    DISCOUNT_TYPE = (
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField()


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)



