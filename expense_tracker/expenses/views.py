from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Expense
from .forms import ExpenseForm


def _get_safe_redirect_url(request):
    referer = request.META.get("HTTP_REFERER")

    if referer and url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return referer

    return reverse("expense_list")


@login_required
def expense_list(request):
    expenses = (
        Expense.objects
        .filter(user=request.user)
        .select_related("category")
        .order_by("-date", "-created_at")
    )
    total_amount = expenses.aggregate(total=Sum("amount"))["total"] or 0
    form = ExpenseForm(user=request.user)

    return render(request, "expenses/expense_list.html", {
        "expenses": expenses,
        "total_amount": total_amount,
        "form": form,
    })


@login_required
@require_POST
def add_expense(request):
    form = ExpenseForm(request.POST, user=request.user)

    if form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.save()
        messages.success(request, "Expense added successfully.")
    else:
        messages.error(request, "Invalid expense form. Please check the entered values.")

    return redirect(_get_safe_redirect_url(request))


@login_required
@require_POST
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST, instance=expense, user=request.user)

    if form.is_valid():
        updated_expense = form.save(commit=False)
        updated_expense.user = request.user
        updated_expense.save()
        messages.success(request, "Expense updated successfully.")
    else:
        messages.error(request, "Invalid expense form. Please check the entered values.")

    return redirect(_get_safe_redirect_url(request))


@login_required
@require_POST
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    messages.success(request, "Expense deleted successfully.")

    return redirect(_get_safe_redirect_url(request))