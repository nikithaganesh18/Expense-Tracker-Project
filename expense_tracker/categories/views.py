from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Category
from .forms import CategoryForm


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).annotate(
        expense_count=Count('expenses')
    )

    return render(request, 'categories/category_list.html', {
        'categories': categories
    })


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
    return redirect('category_list')


@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
    return redirect('category_list')


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == 'POST':
        if not category.expenses.exists():
            category.delete()
    return redirect('category_list')