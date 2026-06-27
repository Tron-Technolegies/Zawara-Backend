import os
import django
from django.test import RequestFactory
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Zawara.settings')
django.setup()

from userapp.views import view_products

factory = RequestFactory()

# Test 1: Simple GET request
request = factory.get('/view_products/')
response = view_products(request)
print("Status:", response.status_code)
content = json.loads(response.content)
print("Total products default:", content.get("total_products"))

# Test 2: Search by name
request = factory.get('/view_products/', {'search': 'test'})
response = view_products(request)
content = json.loads(response.content)
print("Search default test count:", content.get("total_products"))

# Test 3: Search by name param
request = factory.get('/view_products/', {'name': 'test'})
response = view_products(request)
content = json.loads(response.content)
print("Name default test count:", content.get("total_products"))

# Test 4: Price filter (min_price and max_price)
request = factory.get('/view_products/', {'min_price': '10', 'max_price': '1000'})
response = view_products(request)
content = json.loads(response.content)
print("Price min_price/max_price count:", content.get("total_products"))

# Test 5: Size filter
request = factory.get('/view_products/', {'size': 'medium'})
response = view_products(request)
content = json.loads(response.content)
print("Size medium count:", content.get("total_products"))

# Test 6: Material filter
request = factory.get('/view_products/', {'material': 'cotton'})
response = view_products(request)
content = json.loads(response.content)
print("Material cotton count:", content.get("total_products"))
