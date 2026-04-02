from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from categories.models import Category
from expenses.models import Expense
from .models import ReceiptUpload
from .forms import ReceiptUploadForm, ReceiptConfirmForm
from .utils import extract_receipt_data, upload_receipt_to_s3


@login_required
def upload_receipt(request):
    if request.method == "POST":
        form = ReceiptUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES.get("file")

            if not uploaded_file:
                messages.error(request, "Please choose a receipt file.")
                return render(request, "receipt_scanner/upload_receipt.html", {"form": form})

            try:
                file_bytes = uploaded_file.read()
                original_name = uploaded_file.name
                content_type = getattr(uploaded_file, "content_type", None)

                receipt = form.save(commit=False)
                receipt.user = request.user

                s3_key, s3_url = upload_receipt_to_s3(
                    file_bytes=file_bytes,
                    original_name=original_name,
                    content_type=content_type,
                    user_id=request.user.id,
                )
                receipt.s3_key = s3_key
                receipt.s3_url = s3_url

                extracted = extract_receipt_data(
                    file_bytes=file_bytes,
                    original_name=original_name,
                )

                merchant = extracted.get("merchant") or "Unknown Merchant"
                raw_amount = extracted.get("amount", 0)
                receipt_date = extracted.get("date") or timezone.localdate()
                raw_text = extracted.get("raw_text", "")

                try:
                    amount = Decimal(str(raw_amount or 0))
                except (InvalidOperation, TypeError, ValueError):
                    amount = Decimal("0.00")

                receipt.merchant = merchant
                receipt.amount = amount
                receipt.date = receipt_date
                receipt.raw_text = raw_text

                category_name = extracted.get("category_name") or "Other"
                category = Category.objects.filter(
                    user=request.user,
                    name=category_name
                ).first()

                if not category:
                    category, _ = Category.objects.get_or_create(
                        user=request.user,
                        name="Other"
                    )

                receipt.category = category
                receipt.save()

                Expense.objects.create(
                    user=request.user,
                    title=merchant,
                    amount=amount,
                    category=category,
                    date=receipt_date,
                    description=f"Imported from receipt: {merchant}",
                )

                messages.success(
                    request,
                    f"Receipt uploaded successfully. Expense of {amount:.2f} added."
                )
                return redirect("expense_list")

            except Exception as e:
                messages.error(request, f"Receipt processing failed: {str(e)}")
                return render(request, "receipt_scanner/upload_receipt.html", {"form": form})
        else:
            messages.error(request, f"Form validation failed: {form.errors}")
            return render(request, "receipt_scanner/upload_receipt.html", {"form": form})

    else:
        form = ReceiptUploadForm()

    return render(request, "receipt_scanner/upload_receipt.html", {"form": form})


@login_required
def receipt_preview(request, pk):
    receipt = get_object_or_404(ReceiptUpload, pk=pk, user=request.user)

    default_category = receipt.category or Category.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = ReceiptConfirmForm(request.POST, user=request.user)
        if form.is_valid():
            Expense.objects.create(
                user=request.user,
                title=form.cleaned_data["merchant"],
                amount=form.cleaned_data["amount"],
                category=form.cleaned_data["category"],
                date=form.cleaned_data["date"],
                description=form.cleaned_data["description"] or f"Imported from receipt: {receipt.merchant}",
            )
            messages.success(request, "Expense created successfully from receipt.")
            return redirect("expense_list")
    else:
        form = ReceiptConfirmForm(
            initial={
                "merchant": receipt.merchant,
                "amount": receipt.amount,
                "date": receipt.date,
                "category": default_category,
                "description": f"Imported from receipt: {receipt.merchant}",
            },
            user=request.user,
        )

    return render(request, "receipt_scanner/receipt_preview.html", {
        "receipt": receipt,
        "form": form,
    })