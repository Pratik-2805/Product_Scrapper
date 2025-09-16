from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('images/', views.images, name='images'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('test-images/', views.test_image_url, name='test_images'),  # Add this line
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('image-proxy/', views.image_proxy, name='image_proxy'),
]