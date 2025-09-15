from django import forms

from apps.donations.models import Donation


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ["name", "amount"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Enter your name"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "input",
                    "placeholder": "Enter donation amount",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }
        labels = {"name": "Your Name", "amount": "Donation Amount (£)"}
