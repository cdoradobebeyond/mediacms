from decimal import Decimal

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_is_approved"),
        ("files", "0013_page_tinymcemedia"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="currency",
            field=models.CharField(default="USD", help_text="Currency used for the category price", max_length=3),
        ),
        migrations.AddField(
            model_name="category",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text="Price required to unlock the full category",
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="requires_payment",
            field=models.BooleanField(default=False, help_text="Whether access to this category requires payment"),
        ),
        migrations.AddField(
            model_name="media",
            name="currency",
            field=models.CharField(default="USD", help_text="Currency used for the media price", max_length=3),
        ),
        migrations.AddField(
            model_name="media",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text="Price for individual access to this media",
                max_digits=8,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AddField(
            model_name="media",
            name="requires_payment",
            field=models.BooleanField(default=False, help_text="Whether viewing this media requires payment"),
        ),
        migrations.CreateModel(
            name="CategoryPurchase",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchases",
                        to="files.category",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="category_purchases",
                        to="users.user",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"], "unique_together": {("user", "category")}},
        ),
        migrations.CreateModel(
            name="MediaPurchase",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=8,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "media",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchases",
                        to="files.media",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_purchases",
                        to="users.user",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"], "unique_together": {("user", "media")}},
        ),
    ]
