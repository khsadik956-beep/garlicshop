from datetime import date
from decimal import Decimal
from pathlib import Path
import re
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product


NATURAL_CATALOG = [
    ("GS-ATTA-WHEAT-5KG", "GarlicShop Stoneground Wheat Atta 5kg", "Natural Flours", "5kg", "Flour", "Premium Bag", "Chapati and paratha", "Wheat Atta", "329.00"),
    ("GS-ATTA-MULTIGRAIN-5KG", "GarlicShop Multigrain Atta 5kg", "Natural Flours", "5kg", "Flour", "Premium Bag", "Healthy rotis", "Multigrain", "399.00"),
    ("GS-ATTA-JOWAR-1KG", "GarlicShop Jowar Atta 1kg", "Natural Flours", "1kg", "Flour", "Pouch", "Bhakri", "Jowar Atta", "129.00"),
    ("GS-ATTA-BAJRA-1KG", "GarlicShop Bajra Atta 1kg", "Natural Flours", "1kg", "Flour", "Pouch", "Winter rotis", "Bajra Atta", "119.00"),
    ("GS-ATTA-RAGI-1KG", "GarlicShop Ragi Flour 1kg", "Natural Flours", "1kg", "Flour", "Pouch", "Breakfast", "Ragi Flour", "139.00"),
    ("GS-ATTA-BESAN-1KG", "GarlicShop Chana Besan 1kg", "Natural Flours", "1kg", "Flour", "Pouch", "Pakoda and sweets", "Besan", "129.00"),
    ("GS-OIL-GROUNDNUT-1L", "GarlicShop Cold Pressed Groundnut Oil 1L", "Natural Oils", "1L", "Cold Pressed Oil", "Bottle", "Daily cooking", "Groundnut Oil", "299.00"),
    ("GS-OIL-MUSTARD-1L", "GarlicShop Cold Pressed Mustard Oil 1L", "Natural Oils", "1L", "Cold Pressed Oil", "Bottle", "Pickle and cooking", "Mustard Oil", "279.00"),
    ("GS-OIL-SESAME-500", "GarlicShop Wood Pressed Sesame Oil 500ml", "Natural Oils", "500ml", "Wood Pressed Oil", "Bottle", "Traditional cooking", "Sesame Oil", "249.00"),
    ("GS-OIL-COCONUT-500", "GarlicShop Virgin Coconut Oil 500ml", "Natural Oils", "500ml", "Virgin Oil", "Bottle", "Cooking and wellness", "Coconut Oil", "329.00"),
    ("GS-OIL-FLAX-250", "GarlicShop Flaxseed Oil 250ml", "Natural Oils", "250ml", "Seed Oil", "Bottle", "Wellness", "Flax Oil", "229.00"),
    ("GS-HONEY-RAW-250", "GarlicShop Raw Forest Honey 250g", "Natural Sweeteners", "250g", "Honey", "Glass Jar", "Daily wellness", "Raw Honey", "169.00"),
    ("GS-HONEY-MULTIFLORA-500", "GarlicShop Multifloral Honey 500g", "Natural Sweeteners", "500g", "Honey", "Glass Jar", "Tea and breakfast", "Honey", "269.00"),
    ("GS-JAGGERY-CUBE-500", "GarlicShop Jaggery Cubes 500g", "Natural Sweeteners", "500g", "Cubes", "Box", "Tea and snacks", "Jaggery Cubes", "99.00"),
    ("GS-KHAND-1KG", "GarlicShop Desi Khand 1kg", "Natural Sweeteners", "1kg", "Sweetener", "Pouch", "Tea and sweets", "Desi Khand", "149.00"),
    ("GS-MISHRI-500", "GarlicShop Natural Mishri 500g", "Natural Sweeteners", "500g", "Crystals", "Jar", "Prasad and drinks", "Mishri", "119.00"),
    ("GS-ALMOND-250", "GarlicShop California Almonds 250g", "Dry Fruits", "250g", "Nuts", "Pouch", "Daily nutrition", "Almonds", "299.00"),
    ("GS-CASHEW-250", "GarlicShop Whole Cashews 250g", "Dry Fruits", "250g", "Nuts", "Pouch", "Snacks and sweets", "Cashews", "319.00"),
    ("GS-RAISIN-250", "GarlicShop Natural Raisins 250g", "Dry Fruits", "250g", "Dry Fruit", "Pouch", "Snacks", "Raisins", "129.00"),
    ("GS-DATES-500", "GarlicShop Seedless Dates 500g", "Dry Fruits", "500g", "Dates", "Box", "Energy snack", "Dates", "199.00"),
    ("GS-WALNUT-200", "GarlicShop Walnut Kernels 200g", "Dry Fruits", "200g", "Nuts", "Pouch", "Daily nutrition", "Walnuts", "289.00"),
    ("GS-CHIA-250", "GarlicShop Chia Seeds 250g", "Super Seeds", "250g", "Seeds", "Jar", "Smoothies", "Chia", "169.00"),
    ("GS-PUMPKIN-SEED-250", "GarlicShop Pumpkin Seeds 250g", "Super Seeds", "250g", "Seeds", "Jar", "Trail mix", "Pumpkin Seeds", "189.00"),
    ("GS-SUNFLOWER-SEED-250", "GarlicShop Sunflower Seeds 250g", "Super Seeds", "250g", "Seeds", "Jar", "Healthy snacks", "Sunflower", "149.00"),
    ("GS-MELON-SEED-250", "GarlicShop Melon Seeds 250g", "Super Seeds", "250g", "Seeds", "Jar", "Sweets and snacks", "Melon Seeds", "179.00"),
    ("GS-MAKHANA-100", "GarlicShop Roasted Makhana 100g", "Natural Snacks", "100g", "Roasted Snack", "Pouch", "Tea-time snack", "Makhana", "119.00"),
    ("GS-CHANA-ROASTED-500", "GarlicShop Roasted Chana 500g", "Natural Snacks", "500g", "Roasted Snack", "Pouch", "Protein snack", "Roasted Chana", "109.00"),
    ("GS-PEANUT-ROASTED-500", "GarlicShop Roasted Peanuts 500g", "Natural Snacks", "500g", "Roasted Snack", "Pouch", "Evening snack", "Peanuts", "129.00"),
    ("GS-MILLET-MIX-500", "GarlicShop Millet Breakfast Mix 500g", "Natural Snacks", "500g", "Breakfast Mix", "Pouch", "Healthy breakfast", "Millet Mix", "169.00"),
    ("GS-POHA-1KG", "GarlicShop Thick Poha 1kg", "Natural Staples", "1kg", "Flattened Rice", "Pouch", "Breakfast", "Poha", "99.00"),
    ("GS-SABUDANA-1KG", "GarlicShop Sabudana 1kg", "Natural Staples", "1kg", "Pearls", "Pouch", "Fasting meals", "Sabudana", "139.00"),
    ("GS-SUJI-1KG", "GarlicShop Natural Suji 1kg", "Natural Staples", "1kg", "Semolina", "Pouch", "Upma and halwa", "Suji", "89.00"),
    ("GS-DALIA-1KG", "GarlicShop Broken Wheat Dalia 1kg", "Natural Staples", "1kg", "Broken Wheat", "Pouch", "Healthy breakfast", "Dalia", "99.00"),
    ("GS-OATS-1KG", "GarlicShop Rolled Oats 1kg", "Natural Staples", "1kg", "Oats", "Pouch", "Breakfast", "Oats", "199.00"),
    ("GS-HERB-TULSI-100", "GarlicShop Dried Tulsi Leaves 100g", "Herbal Products", "100g", "Dried Leaves", "Jar", "Herbal tea", "Tulsi", "99.00"),
    ("GS-HERB-MORINGA-100", "GarlicShop Moringa Powder 100g", "Herbal Products", "100g", "Powder", "Jar", "Smoothies", "Moringa", "149.00"),
    ("GS-HERB-ASHWAGANDHA-100", "GarlicShop Ashwagandha Powder 100g", "Herbal Products", "100g", "Powder", "Jar", "Wellness", "Ashwagandha", "199.00"),
    ("GS-HERB-TRIPHALA-100", "GarlicShop Triphala Powder 100g", "Herbal Products", "100g", "Powder", "Jar", "Wellness", "Triphala", "159.00"),
    ("GS-MASALA-GARAM-100", "GarlicShop Garam Masala 100g", "Natural Masala", "100g", "Masala", "Jar", "Curries", "Garam Masala", "119.00"),
    ("GS-MASALA-CHAAT-100", "GarlicShop Chaat Masala 100g", "Natural Masala", "100g", "Masala", "Jar", "Snacks", "Chaat Masala", "89.00"),
    ("GS-MASALA-SAMBAR-100", "GarlicShop Sambar Masala 100g", "Natural Masala", "100g", "Masala", "Jar", "South Indian meals", "Sambar Masala", "99.00"),
    ("GS-MASALA-PAVBHAJI-100", "GarlicShop Pav Bhaji Masala 100g", "Natural Masala", "100g", "Masala", "Jar", "Street food", "Pav Bhaji", "99.00"),
    ("GS-SALT-ROCK-1KG", "GarlicShop Sendha Namak 1kg", "Natural Salts", "1kg", "Rock Salt", "Pouch", "Fasting meals", "Rock Salt", "79.00"),
    ("GS-SALT-BLACK-500", "GarlicShop Black Salt 500g", "Natural Salts", "500g", "Salt", "Jar", "Chaat and drinks", "Black Salt", "69.00"),
    ("GS-PICKLE-MANGO-400", "GarlicShop Mango Pickle 400g", "Natural Pickles", "400g", "Pickle", "Glass Jar", "Meals", "Mango Pickle", "159.00"),
    ("GS-PICKLE-LEMON-400", "GarlicShop Lemon Pickle 400g", "Natural Pickles", "400g", "Pickle", "Glass Jar", "Meals", "Lemon Pickle", "149.00"),
    ("GS-PICKLE-MIX-400", "GarlicShop Mixed Veg Pickle 400g", "Natural Pickles", "400g", "Pickle", "Glass Jar", "Paratha", "Mixed Pickle", "169.00"),
    ("GS-PAPAD-URAD-200", "GarlicShop Urad Papad 200g", "Natural Papad", "200g", "Papad", "Pouch", "Meals", "Urad Papad", "99.00"),
    ("GS-PAPAD-MOONG-200", "GarlicShop Moong Papad 200g", "Natural Papad", "200g", "Papad", "Pouch", "Meals", "Moong Papad", "109.00"),
    ("GS-COMBO-NATURAL-1", "GarlicShop Natural Breakfast Combo", "Natural Combos", "Oats + Honey + Seeds", "Combo", "Gift Box", "Breakfast", "Breakfast Combo", "499.00"),
    ("GS-COMBO-KITCHEN-1", "GarlicShop Natural Kitchen Combo", "Natural Combos", "Atta + Oil + Spices", "Combo", "Gift Box", "Monthly kitchen", "Kitchen Combo", "699.00"),
    ("GS-COMBO-HEALTH-1", "GarlicShop Wellness Combo", "Natural Combos", "Honey + Herbs + Seeds", "Combo", "Gift Box", "Wellness", "Wellness Combo", "599.00"),
]


class Command(BaseCommand):
    help = "Create natural grocery and wellness products with GarlicShop branding."

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

    def _palette(self, category):
        palettes = {
            "Natural Flours": ("#80612a", "#e5be62", "#fff5dc"),
            "Natural Oils": ("#6f551c", "#e0ad36", "#fff6d9"),
            "Natural Sweeteners": ("#7b451f", "#d8943a", "#fff0d2"),
            "Dry Fruits": ("#6b3827", "#d9a065", "#fff3e7"),
            "Super Seeds": ("#475b2a", "#a9bd55", "#f4f8de"),
            "Natural Snacks": ("#7b4f1d", "#e0a84b", "#fff2da"),
            "Natural Staples": ("#6d5524", "#d8bc62", "#fff7dc"),
            "Herbal Products": ("#236342", "#80b86b", "#eaf8ef"),
            "Natural Masala": ("#8e3219", "#e28a2e", "#fff0da"),
            "Natural Salts": ("#54616b", "#b8c7d1", "#eef5f7"),
            "Natural Pickles": ("#8c2d19", "#d87931", "#fff0dc"),
            "Natural Papad": ("#725d29", "#d4b45c", "#fff6df"),
            "Natural Combos": ("#243b2a", "#d4af37", "#eef6e8"),
        }
        return palettes.get(category, ("#226439", "#d4af37", "#f7f8f3"))

    def _draw_product_mark(self, draw, center, label, primary, accent):
        cx, cy = center
        draw.rounded_rectangle((cx - 168, cy - 118, cx + 168, cy + 118), radius=30, fill=(255, 255, 255, 226), outline=accent, width=6)
        draw.ellipse((cx - 72, cy - 80, cx + 72, cy + 64), fill=accent)
        draw.arc((cx - 92, cy - 96, cx + 92, cy + 92), 200, 338, fill=primary, width=9)
        draw.line((cx, cy - 92, cx, cy + 78), fill=primary, width=7)
        draw.ellipse((cx - 24, cy - 18, cx + 24, cy + 30), fill=primary)
        draw.text((cx, cy + 132), label.upper()[:20], font=self._font(25, True), fill=primary, anchor="ma")

    def _make_image(self, item):
        sku, name, category, pack, form_factor, container, best_for, label, price = item
        primary, accent, background = self._palette(category)
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "catalog"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._slug(sku)}.png"

        canvas = Image.new("RGB", (900, 650), background)
        draw = ImageDraw.Draw(canvas, "RGBA")

        draw.rounded_rectangle((28, 28, 872, 622), radius=28, fill=(255, 255, 255, 82), outline="#e1d6b2", width=2)
        for i in range(8):
            x = 70 + i * 110
            draw.ellipse((x, 178, x + 56, 234), fill=accent + "55")

        draw.rounded_rectangle((34, 34, 866, 140), radius=18, fill=(8, 9, 8, 224), outline="#d4af37", width=3)
        draw.text((60, 52), "GarlicShop", font=self._font(36, True), fill="#ffffff")
        draw.text((285, 60), "NATURAL PRODUCTS", font=self._font(18, True), fill="#d4af37")
        draw.rounded_rectangle((616, 54, 838, 118), radius=14, fill=primary)
        draw.text((727, 73), category.upper()[:18], font=self._font(17, True), fill="#ffffff", anchor="ma")

        self._draw_product_mark(draw, (450, 312), label, primary, accent)

        draw.rounded_rectangle((54, 472, 846, 614), radius=22, fill=(255, 255, 255, 238), outline="#d4af37", width=3)
        wrapped = textwrap.wrap(name.replace("GarlicShop ", ""), width=27)
        for index, line in enumerate(wrapped[:2]):
            draw.text((82, 492 + index * 35), line, font=self._font(31, True), fill="#111111")
        draw.text((82, 570), f"{pack} | {form_factor}", font=self._font(19, True), fill=primary)
        draw.rounded_rectangle((656, 542, 826, 596), radius=13, fill="#111111")
        draw.text((741, 557), f"Rs. {price}", font=self._font(25, True), fill="#d4af37", anchor="ma")

        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1, percent=105, threshold=3))
        canvas.save(output_path, quality=92)
        return f"products/catalog/{output_path.name}"

    def handle(self, *args, **options):
        for index, item in enumerate(NATURAL_CATALOG, start=1):
            sku, name, category, pack, form_factor, container, best_for, label, price = item
            image_path = self._make_image(item)
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "price": Decimal(price),
                    "image": image_path,
                    "brand": "GarlicShop Natural",
                    "stock_quantity": 45 + (index % 70),
                    "low_stock_threshold": 10,
                    "description": (
                        f"{name} - GarlicShop natural product with clean ingredients, "
                        "premium packing, and quality checked sourcing."
                    ),
                    "category": category,
                    "pack_of": pack,
                    "form_factor": form_factor,
                    "container_type": container,
                    "highlights": (
                        "Natural GarlicShop product\n"
                        "Clean ingredient sourcing\n"
                        "Quality checked batch\n"
                        "Premium hygienic packing"
                    ),
                    "harvest_date": date(2026, 7, 8),
                    "packed_date": date(2026, 7, 24),
                    "shelf_life_days": 180,
                    "aroma_level": "Natural",
                    "taste_profile": "Clean, natural and premium",
                    "best_for": best_for,
                    "is_available": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"GarlicShop natural catalog ready: {len(NATURAL_CATALOG)} products."
        ))
