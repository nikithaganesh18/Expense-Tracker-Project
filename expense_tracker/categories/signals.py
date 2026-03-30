from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category


DEFAULT_CATEGORIES = [
    "Shopping",
    "Groceries",
    "Food",
    "Travel",
    "Bills",
    "Health",
    "Entertainment",
    "Other",
]


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        for category_name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(
                user=instance,
                name=category_name
            )