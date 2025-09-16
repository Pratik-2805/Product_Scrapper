from django.db import models

# Create your models here.

class Product(models.Model):
    product_name = models.CharField(max_length=1000)
    price = models.CharField(max_length=100, blank=True, null=True)
    original_price = models.CharField(max_length=100, blank=True, null=True)
    discount = models.CharField(max_length=50, blank=True, null=True)
    reviews = models.CharField(max_length=100, blank=True, null=True)
    rating = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=10000, blank=True, null=True)
    product_url = models.CharField(max_length=10000)
    username = models.CharField(max_length=1000)
    scraped_at = models.DateTimeField(auto_now_add=True)
    seller = models.CharField(max_length=200, blank=True, null=True)
    availability = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    specifications = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.product_name

class ProductPriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name='price_history', on_delete=models.CASCADE)
    price = models.IntegerField(blank=True, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.price} @ {self.recorded_at}"

# Keep the old Github model for backward compatibility
class Github(models.Model):
    githubuser = models.CharField(max_length=1000)
    imagelink = models.CharField(max_length=10000)
    username = models.CharField(max_length=1000)

    def __str__(self):
        return self.githubuser