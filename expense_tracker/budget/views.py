from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from .models import Budget
from .forms import BudgetForm
from expenses.models import Expense


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).order_by("-month")

    today = date.today()
    current_month = today.replace(day=1)

    current_budget = Budget.objects.filter(
        user=request.user,
        month=current_month
    ).first()

    current_month_spent = Expense.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month
    ).aggregate(total=Sum("amount"))["total"] or