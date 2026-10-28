from django import forms
from django.utils import timezone
from .models import Inquiry, Service


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "service", "area", "preferred_date", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "type": "tel", "placeholder": "+974 XXXX XXXX"}),
            "area": forms.TextInput(attrs={"placeholder": "Area, building and access details"}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe the work or move, item list and any special requirements"}),
        }
        labels = {"service": "Service (optional)", "preferred_date": "Preferred date (optional)", "message": "How can we help?"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True, category__is_active=True)
        self.fields["service"].empty_label = "Choose a service or general enquiry"
        self.fields["preferred_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_preferred_date(self):
        value = self.cleaned_data.get("preferred_date")
        if value and value < timezone.localdate():
            raise forms.ValidationError("Please choose today or a future date.")
        return value

    def clean_name(self):
        value = self.cleaned_data["name"].strip()
        if not value:
            raise forms.ValidationError("Please enter your name.")
        return value

    def clean_message(self):
        value = self.cleaned_data["message"].strip()
        if len(value) < 15:
            raise forms.ValidationError("Please describe your request in at least 15 characters.")
        return value

    def clean_phone(self):
        value = self.cleaned_data["phone"].strip()
        digits = sum(character.isdigit() for character in value)
        if not 8 <= digits <= 15:
            raise forms.ValidationError("Enter a phone number containing 8 to 15 digits.")
        return value
