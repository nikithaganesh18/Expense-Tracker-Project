from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm


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
def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()

    return redirect(request.META.get("HTTP_REFERER", "expense_list"))


@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            updated_expense = form.save(commit=False)
            updated_expense.user = request.user
            updated_expense.save()

    return redirect(request.META.get("HTTP_REFERER", "expense_list"))


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)

    if request.method == "POST":
        expense.delete()

    return redirect(request.META.get("HTTP_REFERER", "expense_list"))