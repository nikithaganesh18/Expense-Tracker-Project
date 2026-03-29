from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('expenses/', include('expenses.urls')),
    path('categories/', include('categories.urls')),
    path('budget/', include('budget.urls')),
    path('receipts/', include('receipt_scanner.urls')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)