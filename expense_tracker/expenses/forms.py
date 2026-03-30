from django import forms
from .models import Expense
from categories.models import Category


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "amount", "category", "date", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["category"].empty_label = "Select category"

        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user).order_by("name")
        else:
            self.fields["category"].queryset = Category.objects.none()