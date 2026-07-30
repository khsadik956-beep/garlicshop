from datetime import date
from decimal import Decimal
from pathlib import Path
import re
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product


CATALOG = [
    ("GS-FRESH-WHITE-250", "GarlicShop White Garlic 250g", "Fresh Garlic", "250g", "Whole Bulbs", "Premium Fresh Pack", "Daily cooking", "whole-garlic.png", "69.00"),
    ("GS-FRESH-WHITE-500", "GarlicShop White Garlic 500g", "Fresh Garlic", "500g", "Whole Bulbs", "Premium Fresh Pack", "Family kitchen", "whole-garlic.png", "129.00"),
    ("GS-FRESH-WHITE-1KG", "GarlicShop White Garlic 1kg", "Fresh Garlic", "1kg", "Whole Bulbs", "Family Pack", "Monthly stocking", "whole-garlic.png", "239.00"),
    ("GS-FRESH-DESI-250", "GarlicShop Desi Garlic 250g", "Fresh Garlic", "250g", "Whole Bulbs", "Fresh Pack", "Strong tadka", "whole-garlic.png", "79.00"),
    ("GS-FRESH-DESI-500", "GarlicShop Desi Garlic 500g", "Fresh Garlic", "500g", "Whole Bulbs", "Fresh Pack", "Indian cooking", "whole-garlic.png", "145.00"),
    ("GS-FRESH-PINK-250", "GarlicShop Pink Garlic 250g", "Fresh Garlic", "250g", "Whole Bulbs", "Fresh Pack", "Sharp flavor", "whole-garlic.png", "89.00"),
    ("GS-FRESH-PINK-500", "GarlicShop Pink Garlic 500g", "Fresh Garlic", "500g", "Whole Bulbs", "Fresh Pack", "Pickle and chutney", "whole-garlic.png", "169.00"),
    ("GS-FRESH-ORGANIC-250", "GarlicShop Organic Garlic 250g", "Organic Garlic", "250g", "Whole Bulbs", "Organic Pack", "Healthy cooking", "whole-garlic.png", "99.00"),
    ("GS-FRESH-ORGANIC-500", "GarlicShop Organic Garlic 500g", "Organic Garlic", "500g", "Whole Bulbs", "Organic Pack", "Family cooking", "whole-garlic.png", "189.00"),
    ("GS-FRESH-SOLO-200", "GarlicShop Solo Garlic 200g", "Premium Garlic", "200g", "Single Clove", "Premium Box", "Roasting", "whole-garlic.png", "119.00"),
    ("GS-FRESH-ELEPHANT-500", "GarlicShop Elephant Garlic 500g", "Premium Garlic", "500g", "Large Bulbs", "Premium Box", "Grill and roast", "whole-garlic.png", "229.00"),
    ("GS-FRESH-BLACK-100", "GarlicShop Black Garlic 100g", "Premium Garlic", "100g", "Aged Garlic", "Jar", "Gourmet cooking", "offer-garlic.png", "249.00"),
    ("GS-FRESH-ROAST-200", "GarlicShop Roasting Garlic 200g", "Fresh Garlic", "200g", "Whole Bulbs", "Roast Pack", "Oven roasting", "whole-garlic.png", "99.00"),
    ("GS-FRESH-JUMBO-1KG", "GarlicShop Jumbo Garlic 1kg", "Fresh Garlic", "1kg", "Large Bulbs", "Family Pack", "Restaurants", "offer-garlic.png", "269.00"),
    ("GS-PEELED-100", "GarlicShop Peeled Garlic 100g", "Peeled Garlic", "100g", "Peeled Cloves", "Fresh Box", "Quick cooking", "pickle.png", "49.00"),
    ("GS-PEELED-200", "GarlicShop Peeled Garlic 200g", "Peeled Garlic", "200g", "Peeled Cloves", "Fresh Box", "Daily cooking", "pickle.png", "89.00"),
    ("GS-PEELED-500", "GarlicShop Peeled Garlic 500g", "Peeled Garlic", "500g", "Peeled Cloves", "Fresh Box", "Hotels", "pickle.png", "199.00"),
    ("GS-CHOPPED-200", "GarlicShop Chopped Garlic 200g", "Ready To Cook", "200g", "Chopped", "Fresh Box", "Fast cooking", "pickle.png", "99.00"),
    ("GS-MINCED-200", "GarlicShop Minced Garlic 200g", "Ready To Cook", "200g", "Minced", "Jar", "Sauces and stir fry", "pickle.png", "109.00"),
    ("GS-PASTE-200", "GarlicShop Garlic Paste 200g", "Ready To Cook", "200g", "Paste", "Jar", "Curries", "pickle.png", "89.00"),
    ("GS-GG-PASTE-200", "GarlicShop Ginger Garlic Paste 200g", "Ready To Cook", "200g", "Paste", "Jar", "Indian cooking", "pickle.png", "99.00"),
    ("GS-POWDER-50", "GarlicShop Garlic Powder 50g", "Garlic Powder", "50g", "Powder", "Jar", "Seasoning", "powder.png", "59.00"),
    ("GS-POWDER-100", "GarlicShop Garlic Powder 100g", "Garlic Powder", "100g", "Powder", "Jar", "Seasoning", "powder.png", "99.00"),
    ("GS-POWDER-250", "GarlicShop Garlic Powder 250g", "Garlic Powder", "250g", "Powder", "Jar", "Snacks and marinades", "powder.png", "199.00"),
    ("GS-POWDER-500", "GarlicShop Garlic Powder 500g", "Garlic Powder", "500g", "Powder", "Bulk Jar", "Restaurants", "powder.png", "369.00"),
    ("GS-POWDER-ROASTED-100", "GarlicShop Roasted Garlic Powder 100g", "Garlic Powder", "100g", "Roasted Powder", "Jar", "Soups and dips", "powder.png", "129.00"),
    ("GS-GRANULES-100", "GarlicShop Garlic Granules 100g", "Garlic Powder", "100g", "Granules", "Jar", "Pizza and pasta", "powder.png", "119.00"),
    ("GS-FLAKES-100", "GarlicShop Garlic Flakes 100g", "Garlic Powder", "100g", "Flakes", "Pouch", "Toppings", "powder.png", "109.00"),
    ("GS-GARLIC-SALT-100", "GarlicShop Garlic Salt 100g", "Seasoning", "100g", "Seasoning", "Jar", "Fries and snacks", "powder.png", "89.00"),
    ("GS-PERI-GARLIC-80", "GarlicShop Peri Peri Garlic Mix 80g", "Seasoning", "80g", "Seasoning", "Jar", "Snacks", "powder.png", "99.00"),
    ("GS-PICKLE-WHITE-200", "GarlicShop White Garlic Pickle 200g", "Garlic Pickle", "200g", "Pickle", "Glass Jar", "Meals", "pickle.png", "129.00"),
    ("GS-PICKLE-WHITE-300", "GarlicShop White Garlic Pickle 300g", "Garlic Pickle", "300g", "Pickle", "Glass Jar", "Paratha", "pickle.png", "169.00"),
    ("GS-PICKLE-SPICY-300", "GarlicShop Spicy Garlic Pickle 300g", "Garlic Pickle", "300g", "Pickle", "Glass Jar", "Spicy meals", "pickle.png", "179.00"),
    ("GS-PICKLE-SWEET-300", "GarlicShop Sweet Garlic Pickle 300g", "Garlic Pickle", "300g", "Pickle", "Glass Jar", "Mild meals", "pickle.png", "179.00"),
    ("GS-PICKLE-CHILLI-300", "GarlicShop Garlic Chilli Pickle 300g", "Garlic Pickle", "300g", "Pickle", "Glass Jar", "Thecha lovers", "pickle.png", "189.00"),
    ("GS-CHUTNEY-150", "GarlicShop Dry Garlic Chutney 150g", "Chutney", "150g", "Dry Chutney", "Jar", "Vada pav", "powder.png", "99.00"),
    ("GS-CHUTNEY-250", "GarlicShop Garlic Peanut Chutney 250g", "Chutney", "250g", "Dry Chutney", "Jar", "Tiffin", "powder.png", "149.00"),
    ("GS-OIL-250", "GarlicShop Garlic Infused Oil 250ml", "Garlic Oil", "250ml", "Infused Oil", "Bottle", "Cooking and dressing", "offer-garlic.png", "199.00"),
    ("GS-OIL-500", "GarlicShop Garlic Infused Oil 500ml", "Garlic Oil", "500ml", "Infused Oil", "Bottle", "Family cooking", "offer-garlic.png", "349.00"),
    ("GS-SAUCE-200", "GarlicShop Garlic Sauce 200g", "Sauce", "200g", "Sauce", "Bottle", "Snacks", "pickle.png", "119.00"),
    ("GS-MAYO-200", "GarlicShop Garlic Mayo 200g", "Sauce", "200g", "Mayo", "Jar", "Sandwich", "pickle.png", "139.00"),
    ("GS-BUTTER-100", "GarlicShop Garlic Butter 100g", "Spread", "100g", "Butter", "Tub", "Garlic bread", "offer-garlic.png", "129.00"),
    ("GS-BULK-FRESH-2KG", "GarlicShop Fresh Garlic Bulk 2kg", "Bulk Garlic", "2kg", "Whole Bulbs", "Bulk Bag", "Small shops", "offer-garlic.png", "499.00"),
    ("GS-BULK-FRESH-5KG", "GarlicShop Fresh Garlic Bulk 5kg", "Bulk Garlic", "5kg", "Whole Bulbs", "Bulk Bag", "Hotels", "offer-garlic.png", "1099.00"),
    ("GS-BULK-FRESH-10KG", "GarlicShop Fresh Garlic Bulk 10kg", "Bulk Garlic", "10kg", "Whole Bulbs", "Bulk Sack", "Resellers", "offer-garlic.png", "2099.00"),
    ("GS-BULK-POWDER-1KG", "GarlicShop Garlic Powder Bulk 1kg", "Bulk Garlic", "1kg", "Powder", "Bulk Jar", "Restaurants", "powder.png", "699.00"),
    ("GS-SEED-500", "GarlicShop Seed Garlic 500g", "Seed Garlic", "500g", "Seed Bulbs", "Farm Bag", "Kitchen garden", "whole-garlic.png", "169.00"),
    ("GS-SEED-1KG", "GarlicShop Seed Garlic 1kg", "Seed Garlic", "1kg", "Seed Bulbs", "Farm Bag", "Farming", "whole-garlic.png", "299.00"),
    ("GS-COMBO-HOME", "GarlicShop Home Kitchen Combo", "Combo Pack", "Fresh + Powder", "Combo", "Gift Box", "Home kitchen", "offer-garlic.png", "299.00"),
    ("GS-COMBO-PREMIUM", "GarlicShop Premium Garlic Combo", "Combo Pack", "Fresh + Pickle + Powder", "Combo", "Gift Box", "Gifting", "offer-garlic.png", "499.00"),
]


class Command(BaseCommand):
    help = "Create 50 GarlicShop branded products with distinct premium catalog images."

    def _font(self, size, bold=False):
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return ImageFont.truetype(candidate, size)
        return ImageFont.load_default()

    def _slug(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def _make_image(self, product):
        sku, name, category, pack, form_factor, container, best_for, base_image, price = product
        source = Path(settings.BASE_DIR).parent / "static" / "images" / base_image
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "catalog"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._slug(sku)}.png"

        image = Image.open(source).convert("RGB")
        image.thumbnail((900, 650), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (900, 650), "#f7f8f3")
        x = (900 - image.width) // 2
        y = (650 - image.height) // 2
        canvas.paste(image, (x, y))
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))
        draw = ImageDraw.Draw(canvas, "RGBA")

        colors = {
            "Fresh Garlic": "#226439",
            "Organic Garlic": "#2f7d32",
            "Premium Garlic": "#111111",
            "Peeled Garlic": "#7a5a24",
            "Ready To Cook": "#5b4b2a",
            "Garlic Powder": "#b8860b",
            "Seasoning": "#8a6115",
            "Garlic Pickle": "#8f2f16",
            "Chutney": "#a14612",
            "Garlic Oil": "#7d681c",
            "Sauce": "#7b1f1f",
            "Spread": "#6b5724",
            "Bulk Garlic": "#143d24",
            "Seed Garlic": "#31542a",
            "Combo Pack": "#1f1f1f",
        }
        accent = colors.get(category, "#226439")

        draw.rounded_rectangle((34, 34, 866, 138), radius=18, fill=(8, 9, 8, 214), outline="#d4af37", width=3)
        draw.text((60, 50), "GarlicShop", font=self._font(35, True), fill="#ffffff")
        draw.text((278, 57), "PREMIUM BRAND", font=self._font(18, True), fill="#d4af37")
        draw.rounded_rectangle((650, 52, 838, 116), radius=13, fill=accent)
        draw.text((744, 70), category.upper()[:17], font=self._font(18, True), fill="#ffffff", anchor="ma")

        draw.rounded_rectangle((50, 450, 850, 616), radius=22, fill=(255, 255, 255, 230), outline="#d4af37", width=3)
        title_font = self._font(33, True)
        wrapped = textwrap.wrap(name.replace("GarlicShop ", ""), width=26)
        for index, line in enumerate(wrapped[:2]):
            draw.text((78, 470 + index * 38), line, font=title_font, fill="#111111")

        draw.text((78, 558), f"{pack} | {form_factor}", font=self._font(20, True), fill=accent)
        draw.text((78, 586), f"Best for: {best_for}", font=self._font(17), fill="#444444")
        draw.rounded_rectangle((660, 542, 824, 596), radius=13, fill="#111111")
        draw.text((742, 557), f"Rs. {price}", font=self._font(25, True), fill="#d4af37", anchor="ma")

        canvas.save(output_path, quality=92)
        return f"products/catalog/{output_path.name}"

    def handle(self, *args, **options):
        catalog_skus = [product[0] for product in CATALOG]
        Product.objects.exclude(sku__in=catalog_skus).update(is_available=False)

        for index, product in enumerate(CATALOG, start=1):
            sku, name, category, pack, form_factor, container, best_for, base_image, price = product
            image_path = self._make_image(product)
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "price": Decimal(price),
                    "image": image_path,
                    "brand": "GarlicShop",
                    "stock_quantity": 35 + (index % 55),
                    "low_stock_threshold": 8,
                    "description": (
                        f"{name} - GarlicShop branded {category.lower()} product with "
                        "clean packing, farm selected quality, and freshness tracking."
                    ),
                    "category": category,
                    "pack_of": pack,
                    "form_factor": form_factor,
                    "container_type": container,
                    "highlights": (
                        "GarlicShop branded pack\n"
                        "Farm selected quality\n"
                        "Freshness checked\n"
                        "Clean premium packing"
                    ),
                    "harvest_date": date(2026, 7, 1),
                    "packed_date": date(2026, 7, 12),
                    "shelf_life_days": 60,
                    "aroma_level": "Strong" if "Fresh" in category or "Pickle" in category else "Medium",
                    "taste_profile": "Fresh, bold and aromatic",
                    "best_for": best_for,
                    "is_available": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"GarlicShop catalog ready: {len(CATALOG)} products. Extra products hidden."
        ))
