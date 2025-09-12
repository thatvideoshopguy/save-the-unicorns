from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Donation(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.amount}"

    class Meta:
        ordering = ["-created_at"]
