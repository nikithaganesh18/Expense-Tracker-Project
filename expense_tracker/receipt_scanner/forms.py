from django import forms
from .models import ReceiptUpload
from categories.models import Category


class ReceiptUploadForm(forms.ModelForm):
    class Meta:
        model = ReceiptUpload
        fields = ['file']


class ReceiptConfirmForm(forms.Form):
    merchant = forms.CharField(max_length=255)
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    category = forms.ModelChoiceField(queryset=Category.objects.none())
    description = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user).order_by('name')