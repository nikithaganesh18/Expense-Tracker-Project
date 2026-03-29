from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Budget
from .forms import BudgetForm
from expenses.models import Expense


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).order_by('-month')

    return render(request, 'budget/budget_list.html', {
        'budgets': budgets
    })


@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.month = budget.month.replace(day=1)
            Budget.objects.update_or_create(
                user=request.user,
                month=budget.month,
                defaults={'amount': budget.amount}
            )
    return redirect(request.META.get('HTTP_REFERER', 'budget_list'))


@login_required
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            edited_budget = form.save(commit=False)
            edited_budget.month = edited_budget.month.replace(day=1)
            edited_budget.save()
    return redirect(request.META.get('HTTP_REFERER', 'budget_list'))


@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)

    if request.method == 'POST':
        budget.delete()
    return redirect(request.META.get('HTTP_REFERER', 'budget_list'))