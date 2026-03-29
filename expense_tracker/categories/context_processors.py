from .models import Category


def user_categories(request):
    if request.user.is_authenticated:
        categories = Category.objects.filter(user=request.user).order_by('name')
    else:
        categories = Category.objects.none()

    return {'user_categories': categories}