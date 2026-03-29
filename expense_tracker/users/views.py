from datetime import date, timedelta
from calendar import month_abbr

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Sum

from .forms import RegisterForm
from expenses.models import Expense
from budget.models import Budget


def home_view(request):
    return render(request, 'users/home.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # ✅ Trigger welcome popup
            request.session['show_welcome'] = True

            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_month_last_day = first_day_this_month - timedelta(days=1)

    # Current month expenses
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=today.year,
        date__month=today.month
    )

    # Last month expenses
    last_month_expenses = Expense.objects.filter(
        user=request.user,
        date__year=last_month_last_day.year,
        date__month=last_month_last_day.month
    )

    # Totals
    this_month_total = current_month_expenses.aggregate(total=Sum('amount'))['total'] or 0
    last_month_total = last_month_expenses.aggregate(total=Sum('amount'))['total'] or 0
    all_time_total = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or 0
    expense_count = current_month_expenses.count()

    # Budget
    current_budget = Budget.objects.filter(
        user=request.user,
        month=first_day_this_month
    ).first()

    budget_amount = current_budget.amount if current_budget else 0
    budget_used_amount = this_month_total
    budget_percentage = 0

    if budget_amount and budget_amount > 0:
        budget_percentage = min(round((budget_used_amount / budget_amount) * 100, 2), 100)

    if current_budget:
        budget_used = f"{this_month_total} / {current_budget.amount}"
    else:
        budget_used = "No budget"

    # 📊 Monthly trend (last 6 months)
    monthly_labels = []
    monthly_data = []

    for i in range(5, -1, -1):
        ref_month = today.month - i
        ref_year = today.year

        while ref_month <= 0:
            ref_month += 12
            ref_year -= 1

        total = Expense.objects.filter(
            user=request.user,
            date__year=ref_year,
            date__month=ref_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_labels.append(f"{month_abbr[ref_month]} '{str(ref_year)[-2:]}")
        monthly_data.append(float(total))

    # 📊 Category breakdown
    category_expenses = current_month_expenses.values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    category_labels = [item['category__name'] for item in category_expenses]
    category_data = [float(item['total']) for item in category_expenses]

    # ✅ Show welcome popup only once
    show_welcome = request.session.pop('show_welcome', False)

    context = {
        "this_month": this_month_total,
        "last_month": last_month_total,
        "budget_used": budget_used,
        "all_time": all_time_total,
        "expense_count": expense_count,
        "budget_amount": budget_amount,
        "budget_used_amount": budget_used_amount,
        "budget_percentage": budget_percentage,
        "monthly_labels": monthly_labels,
        "monthly_data": monthly_data,
        "category_labels": category_labels,
        "category_data": category_data,
        "show_welcome": show_welcome,
    }

    return render(request, "users/dashboard.html", context)