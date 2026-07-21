from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("store", "0009_wishlistitem"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, default="", max_length=150)),
                ("phone", models.CharField(blank=True, default="", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="customer_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CustomerAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("label", models.CharField(choices=[("home", "Home"), ("work", "Work"), ("other", "Other")], default="home", max_length=20)),
                ("full_name", models.CharField(max_length=150)),
                ("phone", models.CharField(max_length=20)),
                ("pincode", models.CharField(max_length=6)),
                ("address_line", models.TextField()),
                ("area", models.CharField(blank=True, default="", max_length=150)),
                ("city", models.CharField(blank=True, default="", max_length=100)),
                ("state", models.CharField(blank=True, default="", max_length=100)),
                ("country", models.CharField(default="India", max_length=80)),
                ("is_default", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="addresses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-is_default", "-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="BuyLaterItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="buy_later_by", to="store.product")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="buy_later_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
                "unique_together": {("user", "product")},
            },
        ),
    ]
