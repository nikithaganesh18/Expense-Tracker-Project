from django.urls import path
from .views import category_list, add_category, edit_category, delete_category

urlpatterns = [
    path('', category_list, name='category_list'),
    path('add/', add_category, name='add_category'),
    path('edit/<int:pk>/', edit_category, name='edit_category'),
    path('delete/<int:pk>/', delete_category, name='delete_category'),
]