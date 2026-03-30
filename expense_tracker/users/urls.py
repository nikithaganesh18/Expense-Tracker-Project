from django.urls import path
from .views import home_view, dashboard_view, register_view, login_view, logout_view

urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]