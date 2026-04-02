from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Budget
from .forms import BudgetForm


def _normalize_month(month_value):
    return month_value.replace(day=1)


def _get_safe_redirect_url(request):
    referer = request.META.get("HTTP_REFERER")

    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return referer

    return reverse("budget_list")


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).order_by("-month")
    form = BudgetForm()

    return render(request, "budget/budget_list.html", {
        "budgets": budgets,
        "form": form,
    })


@login_required
@require_POST
def add_budget(request):
    form = BudgetForm(request.POST)

    if form.is_valid():
        budget = form.save(commit=False)
        budget.user = request.user
        budget.month = _normalize_month(budget.month)

        _, created = Budget.objects.update_or_create(
            user=request.user,
            month=budget.month,
            defaults={"amount": budget.amount},
        )

        if created:
            messages.success(request, "Budget added successfully.")
        else:
            messages.success(request, "Budget for this month already existed and has been updated.")
    else:
        messages.error(request, "Invalid budget form. Please check the entered values.")

    return redirect(_get_safe_redirect_url(request))


@login_required
@require_POST
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    form = BudgetForm(request.POST, instance=budget)

    if form.is_valid():
        edited_budget = form.save(commit=False)
        edited_budget.user = request.user
        edited_budget.month = _normalize_month(edited_budget.month)

        existing_budget = Budget.objects.filter(
            user=request.user,
            month=edited_budget.month
        ).exclude(pk=budget.pk).first()

        if existing_budget:
            existing_budget.amount = edited_budget.amount
            existing_budget.save()
            budget.delete()
            messages.success(request, "Budget updated successfully. Existing month budget was merged.")
        else:
            edited_budget.save()
            messages.success(request, "Budget updated successfully.")
    else:
        messages.error(request, "Invalid budget form. Please check the entered values.")

    return redirect(_get_safe_redirect_url(request))


@login_required
@require_POST
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, "Budget deleted successfully.")

    return redirect(_get_safe_redirect_url(request))