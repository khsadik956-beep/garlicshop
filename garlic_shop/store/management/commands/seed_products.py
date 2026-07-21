from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from store.models import Product


class Command(BaseCommand):
    help = "Add ready-to-sell GarlicShop products."

    def handle(self, *args, **options):
        products = [
            {
                "sku": "GS-FRESH-250",
                "name": "GarlicShop Fresh White Garlic 250g",
                "price": "69.00",
                "image": "products/garlicshop-premium-whole-garlic.png",
                "stock_quantity": 80,
                "category": "Fresh Garlic",
                "pack_of": "250g",
                "form_factor": "Whole Bulbs",
                "container_type": "Net Bag",
                "aroma_level": "Strong",
                "taste_profile": "Sharp and fresh",
                "best_for": "Daily cooking",
            },
            {
                "sku": "GS-FRESH-500",
                "name": "GarlicShop Premium Farm Garlic 500g",
                "price": "129.00",
                "image": "products/garlicshop-premium-whole-garlic.png",
                "stock_quantity": 65,
                "category": "Fresh Garlic",
                "pack_of": "500g",
                "form_factor": "Whole Bulbs",
                "container_type": "Net Bag",
                "aroma_level": "Bold",
                "taste_profile": "Fresh and punchy",
                "best_for": "Family kitchen",
            },
            {
                "sku": "GS-FRESH-1KG",
                "name": "GarlicShop Organic Family Pack 1kg",
                "price": "239.00",
                "image": "products/garlicshop-premium-offer.png",
                "stock_quantity": 45,
                "category": "Organic Garlic",
                "pack_of": "1kg",
                "form_factor": "Whole Bulbs",
                "container_type": "Eco Pouch",
                "aroma_level": "Strong",
                "taste_profile": "Earthy and bold",
                "best_for": "Monthly stocking",
            },
            {
                "sku": "GS-POWDER-100",
                "name": "GarlicShop Garlic Powder 100g",
                "price": "99.00",
                "image": "products/garlicshop-premium-powder.png",
                "stock_quantity": 90,
                "category": "Garlic Powder",
                "pack_of": "100g",
                "form_factor": "Powder",
                "container_type": "Jar",
                "aroma_level": "Medium",
                "taste_profile": "Smooth and savory",
                "best_for": "Seasoning and marinades",
            },
            {
                "sku": "GS-POWDER-250",
                "name": "GarlicShop Kitchen Garlic Powder 250g",
                "price": "199.00",
                "image": "products/garlicshop-premium-powder.png",
                "stock_quantity": 55,
                "category": "Garlic Powder",
                "pack_of": "250g",
                "form_factor": "Powder",
                "container_type": "Pouch",
                "aroma_level": "Medium",
                "taste_profile": "Balanced and warm",
                "best_for": "Restaurants and snacks",
            },
            {
                "sku": "GS-PICKLE-300",
                "name": "GarlicShop White Garlic Pickle 300g",
                "price": "149.00",
                "image": "products/garlicshop-premium-pickle.png",
                "stock_quantity": 35,
                "category": "Garlic Pickle",
                "pack_of": "300g",
                "form_factor": "Pickle",
                "container_type": "Glass Jar",
                "aroma_level": "Spicy",
                "taste_profile": "Tangy and hot",
                "best_for": "Meals and paratha",
            },
            {
                "sku": "GS-SEED-1KG",
                "name": "GarlicShop Seed Garlic for Farming 1kg",
                "price": "299.00",
                "image": "products/garlicshop-premium-whole-garlic.png",
                "stock_quantity": 28,
                "category": "Seed Garlic",
                "pack_of": "1kg",
                "form_factor": "Seed Bulbs",
                "container_type": "Farm Bag",
                "aroma_level": "Strong",
                "taste_profile": "Farm grade",
                "best_for": "Kitchen garden and farming",
            },
            {
                "sku": "GS-PEELED-200",
                "name": "GarlicShop Peeled Garlic Ready Pack 200g",
                "price": "89.00",
                "image": "products/garlicshop-premium-pickle.png",
                "stock_quantity": 40,
                "category": "Peeled Garlic",
                "pack_of": "200g",
                "form_factor": "Peeled Cloves",
                "container_type": "Fresh Box",
                "aroma_level": "Strong",
                "taste_profile": "Fresh and clean",
                "best_for": "Quick cooking",
            },
            {
                "sku": "GS-BULK-5KG",
                "name": "GarlicShop Bulk Garlic Bag 5kg",
                "price": "1099.00",
                "image": "products/garlicshop-premium-offer.png",
                "stock_quantity": 18,
                "category": "Bulk Garlic",
                "pack_of": "5kg",
                "form_factor": "Whole Bulbs",
                "container_type": "Bulk Sack",
                "aroma_level": "Bold",
                "taste_profile": "Fresh mandi grade",
                "best_for": "Hotels and resellers",
            },
            {
                "sku": "GS-COMBO-STARTER",
                "name": "GarlicShop Starter Combo Pack",
                "price": "349.00",
                "image": "products/garlicshop-premium-offer.png",
                "stock_quantity": 30,
                "category": "Combo Pack",
                "pack_of": "Fresh + Powder + Pickle",
                "form_factor": "Combo",
                "container_type": "Gift Box",
                "aroma_level": "Mixed",
                "taste_profile": "Fresh, spicy and savory",
                "best_for": "Trial and gifting",
            },
        ]

        for data in products:
            data["price"] = Decimal(data["price"])
            data["brand"] = "GarlicShop"
            data["description"] = (
                f"{data['name']} - farm selected quality garlic product with "
                "freshness tracking and clean packing."
            )
            data["highlights"] = (
                "Farm selected batch\n"
                "Fresh packing\n"
                "Quality checked\n"
                "Fast local delivery"
            )
            data["harvest_date"] = date(2026, 6, 20)
            data["packed_date"] = date(2026, 7, 8)
            data["shelf_life_days"] = 45
            data["low_stock_threshold"] = 8
            data["is_available"] = True
            Product.objects.update_or_create(sku=data["sku"], defaults=data)

        self.stdout.write(self.style.SUCCESS(f"Products ready: {Product.objects.count()}"))



