from datetime import date
from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum
from django.utils import timezone

from .forms import RegisterForm
from expenses.models import Expense
from budget.models import Budget


def _month_start(value):
    return value.replace(day=1)


def _next_month_start(value):
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _shift_month(value, offset):
    month_index = value.month - 1 + offset
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def home_view(request):
    return render(request, "users/home.html")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session["show_welcome"] = True
            return redirect("dashboard")
    else:
        form = AuthenticationForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    current_month_start = _month_start(today)
    next_month_start = _next_month_start(current_month_start)
    last_month_start = _shift_month(current_month_start, -1)

    all_expenses = Expense.objects.filter(user=request.user)

    # Current month expenses based only on actual expense date
    current_month_expenses = all_expenses.filter(
        date__gte=current_month_start,
        date__lt=next_month_start
    )

    # Last month expenses based only on actual expense date
    last_month_expenses = all_expenses.filter(
        date__gte=last_month_start,
        date__lt=current_month_start
    )

    # Totals
    this_month_total = current_month_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    last_month_total = last_month_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    all_time_total = all_expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    expense_count = current_month_expenses.count()

    # Current month budget
    current_budget = Budget.objects.filter(
        user=request.user,
        month=current_month_start
    ).first()

    budget_amount = current_budget.amount if current_budget else Decimal("0.00")
    budget_used_amount = this_month_total
    budget_percentage = 0

    if budget_amount > 0:
        budget_percentage = min(round((float(budget_used_amount) / float(budget_amount)) * 100, 2), 100)

    if current_budget:
        budget_used = f"{budget_used_amount:.2f} / {budget_amount:.2f}"
    else:
        budget_used = "No budget"

    # Monthly trend for last 6 months
    monthly_labels = []
    monthly_data = []

    for i in range(5, -1, -1):
        ref_month_start = _shift_month(current_month_start, -i)
        ref_next_month_start = _next_month_start(ref_month_start)

        total = all_expenses.filter(
            date__gte=ref_month_start,
            date__lt=ref_next_month_start
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        monthly_labels.append(ref_month_start.strftime("%b '%y"))
        monthly_data.append(float(total))

    # Category breakdown for current month
    category_expenses = current_month_expenses.values("category__name").annotate(
        total=Sum("amount")
    ).order_by("-total")

    category_labels = [item["category__name"] or "Uncategorized" for item in category_expenses]
    category_data = [float(item["total"]) for item in category_expenses]

    show_welcome = request.session.pop("show_welcome", False)

    context = {
        "this_month": this_month_total,
        "last_month": last_month_total,
        "budget_used": budget_used,
        "all_time": all_time_total,
        "expense_count": expense_count,
        "budget_amount": float(budget_amount),
        "budget_used_amount": float(budget_used_amount),
        "budget_percentage": budget_percentage,
        "monthly_labels": monthly_labels,
        "monthly_data": monthly_data,
        "category_labels": category_labels,
        "category_data": category_data,
        "show_welcome": show_welcome,
    }

    return render(request, "users/dashboard.html", context)