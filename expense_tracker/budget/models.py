from django.db import models
from django.contrib.auth.models import User


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField(help_text="Use the first day of the month")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.user.username} - {self.month} - {self.amount}"