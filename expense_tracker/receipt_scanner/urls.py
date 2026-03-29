from django.urls import path
from .views import upload_receipt, receipt_preview

urlpatterns = [
    path('', upload_receipt, name='upload_receipt'),
    path('preview/<int:pk>/', receipt_preview, name='receipt_preview'),
]