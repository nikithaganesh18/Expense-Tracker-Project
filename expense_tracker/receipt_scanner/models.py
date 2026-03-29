from django.db import models
from django.contrib.auth.models import User
from categories.models import Category


class ReceiptUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='receipts/')
    s3_key = models.CharField(max_length=500, blank=True, null=True)
    s3_url = models.URLField(blank=True, null=True)
    merchant = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    raw_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.file.name}"