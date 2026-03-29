from django.urls import path
from .views import expense_list, add_expense, edit_expense, delete_expense

urlpatterns = [
    path('', expense_list, name='expense_list'),
    path('add/', add_expense, name='add_expense'),
    path('edit/<int:pk>/', edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', delete_expense, name='delete_expense'),
]