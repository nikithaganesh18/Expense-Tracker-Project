from django.urls import path
from .views import budget_list, add_budget, edit_budget, delete_budget

urlpatterns = [
    path('', budget_list, name='budget_list'),
    path('add/', add_budget, name='add_budget'),
    path('edit/<int:pk>/', edit_budget, name='edit_budget'),
    path('delete/<int:pk>/', delete_budget, name='delete_budget'),
]