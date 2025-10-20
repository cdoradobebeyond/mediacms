from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class MediaPurchase(models.Model):
    """Represents a completed purchase that grants access to a media item."""

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='media_purchases')
    media = models.ForeignKey('Media', on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'media')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.media.title} ({self.amount} {self.currency})"


class CategoryPurchase(models.Model):
    """Represents a completed purchase that grants access to a category."""

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='category_purchases')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'category')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.category.title} ({self.amount} {self.currency})"
