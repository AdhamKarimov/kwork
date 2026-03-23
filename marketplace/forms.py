from django import forms
from .models import Order, Tag


class OrderCreateForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Teglar"
    )

    class Meta:
        model = Order
        fields = ['title', 'description', 'initial_budget', 'tags']
        labels = {
            'title': 'Loyiha sarlavhasi',
            'description': 'Batafsil tushuntirish',
            'initial_budget': 'Boshlang\'ich byudjet ($)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: Django REST API yozish'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'initial_budget': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean_initial_budget(self):
        budget = self.cleaned_data.get('initial_budget')
        if budget and budget <= 0:
            raise forms.ValidationError("Byudjet 0 dan katta bo'lishi kerak.")
        return budget
