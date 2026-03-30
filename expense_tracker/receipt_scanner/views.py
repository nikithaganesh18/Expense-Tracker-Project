from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
                return redirect("upload_receipt")

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

                receipt.merchant = extracted.get("merchant", "Unknown Merchant")
                receipt.amount = extracted.get("amount", 0)
                receipt.date = extracted.get("date")
                receipt.raw_text = extracted.get("raw_text", "")

                category_name = extracted.get("category_name")
                category = Category.objects.filter(
                    user=request.user,
                    name=category_name
                ).first()
                receipt.category = category

                receipt.save()
                return redirect("receipt_preview", pk=receipt.pk)

            except Exception as e:
                messages.error(request, f"Receipt processing failed: {str(e)}")
                return redirect("upload_receipt")
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