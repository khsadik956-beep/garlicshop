from datetime import date
from decimal import Decimal
from pathlib import Path
import re
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product


RAW_FARM_CATALOG = [
    ("GS-RAW-ONION-RED-1KG", "GarlicShop Natural Red Onion 1kg", "Natural Farm Produce", "1kg", "Whole Onion", "Mesh Bag", "Daily cooking", "Red Onion", "49.00"),
    ("GS-RAW-ONION-RED-5KG", "GarlicShop Natural Red Onion 5kg", "Natural Farm Produce", "5kg", "Whole Onion", "Mesh Bag", "Family kitchen", "Red Onion", "219.00"),
    ("GS-RAW-ONION-WHITE-1KG", "GarlicShop Natural White Onion 1kg", "Natural Farm Produce", "1kg", "Whole Onion", "Mesh Bag", "Salad and cooking", "White Onion", "59.00"),
    ("GS-RAW-MAKKA-1KG", "GarlicShop Natural Makka 1kg", "Natural Grains", "1kg", "Maize Grain", "Pouch", "Roasting and flour", "Makka", "89.00"),
    ("GS-RAW-MAKKA-5KG", "GarlicShop Natural Makka 5kg", "Natural Grains", "5kg", "Maize Grain", "Farm Bag", "Monthly stock", "Makka", "399.00"),
    ("GS-RAW-SOYABEAN-1KG", "GarlicShop Natural Soyabean 1kg", "Natural Oilseeds", "1kg", "Soybean", "Pouch", "Protein meals", "Soyabean", "119.00"),
    ("GS-RAW-SOYABEAN-5KG", "GarlicShop Natural Soyabean 5kg", "Natural Oilseeds", "5kg", "Soybean", "Farm Bag", "Bulk kitchen", "Soyabean", "549.00"),
    ("GS-RAW-WHEAT-1KG", "GarlicShop Natural Wheat 1kg", "Natural Grains", "1kg", "Whole Grain", "Pouch", "Flour milling", "Wheat", "79.00"),
    ("GS-RAW-WHEAT-5KG", "GarlicShop Natural Wheat 5kg", "Natural Grains", "5kg", "Whole Grain", "Farm Bag", "Home atta", "Wheat", "349.00"),
    ("GS-RAW-RICE-1KG", "GarlicShop Natural Rice 1kg", "Natural Grains", "1kg", "Rice Grain", "Pouch", "Daily meals", "Rice", "99.00"),
    ("GS-RAW-RICE-5KG", "GarlicShop Natural Rice 5kg", "Natural Grains", "5kg", "Rice Grain", "Farm Bag", "Family meals", "Rice", "469.00"),
    ("GS-RAW-CHANA-1KG", "GarlicShop Natural Chana 1kg", "Natural Pulses", "1kg", "Whole Pulse", "Pouch", "Chole and snacks", "Chana", "129.00"),
    ("GS-RAW-TUR-1KG", "GarlicShop Natural Tur 1kg", "Natural Pulses", "1kg", "Whole Pulse", "Pouch", "Dal milling", "Tur", "149.00"),
    ("GS-RAW-MOONG-1KG", "GarlicShop Natural Moong 1kg", "Natural Pulses", "1kg", "Whole Pulse", "Pouch", "Sprouts and dal", "Moong", "139.00"),
    ("GS-RAW-URAD-1KG", "GarlicShop Natural Urad 1kg", "Natural Pulses", "1kg", "Whole Pulse", "Pouch", "Dal and idli", "Urad", "159.00"),
    ("GS-RAW-GROUNDNUT-1KG", "GarlicShop Natural Groundnut 1kg", "Natural Oilseeds", "1kg", "Whole Nut", "Pouch", "Chutney and snacks", "Groundnut", "169.00"),
    ("GS-RAW-MUSTARD-1KG", "GarlicShop Natural Mustard 1kg", "Natural Oilseeds", "1kg", "Seeds", "Pouch", "Oil and pickle", "Mustard", "139.00"),
    ("GS-RAW-SESAME-500G", "GarlicShop Natural Sesame 500g", "Natural Oilseeds", "500g", "Seeds", "Pouch", "Laddu and garnish", "Sesame", "149.00"),
    ("GS-RAW-POTATO-2KG", "GarlicShop Natural Potato 2kg", "Natural Farm Produce", "2kg", "Whole Tuber", "Mesh Bag", "Daily cooking", "Potato", "79.00"),
    ("GS-RAW-GINGER-250G", "GarlicShop Natural Ginger 250g", "Natural Farm Produce", "250g", "Rhizome", "Fresh Pack", "Tea and curry", "Ginger", "69.00"),
    ("GS-RAW-TURMERIC-250G", "GarlicShop Natural Raw Turmeric 250g", "Natural Farm Produce", "250g", "Fresh Root", "Fresh Pack", "Pickle and cooking", "Raw Turmeric", "79.00"),
    ("GS-RAW-GREEN-CHILLI-250G", "GarlicShop Natural Green Chilli 250g", "Natural Farm Produce", "250g", "Fresh Chilli", "Fresh Pack", "Spicy cooking", "Green Chilli", "49.00"),
    ("GS-RAW-LEMON-500G", "GarlicShop Natural Lemon 500g", "Natural Farm Produce", "500g", "Fresh Citrus", "Fresh Pack", "Drinks and pickle", "Lemon", "59.00"),
    ("GS-RAW-CORIANDER-250G", "GarlicShop Natural Coriander Leaves 250g", "Natural Greens", "250g", "Fresh Leaves", "Fresh Pack", "Garnish", "Coriander", "39.00"),
    ("GS-RAW-METHI-250G", "GarlicShop Natural Methi Leaves 250g", "Natural Greens", "250g", "Fresh Leaves", "Fresh Pack", "Sabzi", "Methi", "45.00"),
    ("GS-RAW-TOMATO-1KG", "GarlicShop Natural Tomato 1kg", "Natural Farm Produce", "1kg", "Fresh Tomato", "Fresh Pack", "Daily cooking", "Tomato", "69.00"),
    ("GS-RAW-BRINJAL-1KG", "GarlicShop Natural Brinjal 1kg", "Natural Farm Produce", "1kg", "Fresh Vegetable", "Fresh Pack", "Sabzi", "Brinjal", "59.00"),
    ("GS-RAW-OKRA-500G", "GarlicShop Natural Bhindi 500g", "Natural Farm Produce", "500g", "Fresh Vegetable", "Fresh Pack", "Sabzi", "Bhindi", "49.00"),
    ("GS-RAW-CABBAGE-1PC", "GarlicShop Natural Cabbage 1pc", "Natural Farm Produce", "1pc", "Fresh Vegetable", "Fresh Pack", "Salad and sabzi", "Cabbage", "45.00"),
    ("GS-RAW-CAULIFLOWER-1PC", "GarlicShop Natural Cauliflower 1pc", "Natural Farm Produce", "1pc", "Fresh Vegetable", "Fresh Pack", "Sabzi", "Cauliflower", "59.00"),
    ("GS-RAW-COTTON-SEED-1KG", "GarlicShop Natural Cotton Seed 1kg", "Natural Farm Seeds", "1kg", "Seeds", "Farm Pack", "Farming", "Cotton Seed", "189.00"),
    ("GS-RAW-CORIANDER-SEED-500G", "GarlicShop Natural Coriander Seed 500g", "Natural Farm Seeds", "500g", "Seeds", "Farm Pack", "Kitchen garden", "Coriander Seed", "99.00"),
]


class Command(BaseCommand):
    help = "Create raw natural farm products such as onion, makka, soybean, grains, pulses, and vegetables."

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
            "Natural Farm Produce": ("#236b38", "#8fcf63", "#edf8e8"),
            "Natural Grains": ("#79531d", "#dfbd58", "#fff5d8"),
            "Natural Pulses": ("#8a5a16", "#e5a83c", "#fff0d0"),
            "Natural Oilseeds": ("#4d6128", "#b6c95a", "#f0f7d8"),
            "Natural Greens": ("#1f7545", "#77c66c", "#eaf8ee"),
            "Natural Farm Seeds": ("#345c2f", "#a9be58", "#f2f8de"),
        }
        return palettes.get(category, ("#226439", "#d4af37", "#f7f8f3"))

    def _draw_natural_icon(self, draw, center, label, primary, accent):
        cx, cy = center
        draw.ellipse((cx - 150, cy - 120, cx + 150, cy + 120), fill=(255, 255, 255, 230), outline=accent, width=7)
        label_lower = label.lower()
        if "onion" in label_lower:
            draw.ellipse((cx - 58, cy - 45, cx + 58, cy + 70), fill="#c9556f", outline=primary, width=5)
            draw.polygon([(cx, cy - 92), (cx - 34, cy - 34), (cx + 34, cy - 34)], fill="#79b35b")
            draw.arc((cx - 48, cy - 20, cx + 48, cy + 76), 200, 340, fill="#ffffff", width=4)
        elif "makka" in label_lower:
            draw.rounded_rectangle((cx - 38, cy - 92, cx + 38, cy + 82), radius=34, fill="#f0c738", outline=primary, width=5)
            for x in range(cx - 22, cx + 25, 22):
                for y in range(cy - 65, cy + 66, 25):
                    draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill="#fff4a3")
            draw.polygon([(cx - 70, cy - 20), (cx - 36, cy + 88), (cx - 12, cy + 8)], fill="#4f8a3b")
            draw.polygon([(cx + 70, cy - 20), (cx + 36, cy + 88), (cx + 12, cy + 8)], fill="#4f8a3b")
        elif "soy" in label_lower or "bean" in label_lower:
            for offset in (-42, 0, 42):
                draw.ellipse((cx + offset - 32, cy - 28, cx + offset + 32, cy + 36), fill="#d9c16a", outline=primary, width=4)
        else:
            for offset in (-56, -18, 20, 58):
                draw.ellipse((cx + offset - 22, cy - 52, cx + offset + 22, cy + 54), fill=accent, outline=primary, width=4)
            draw.arc((cx - 100, cy - 88, cx + 100, cy + 90), 18, 162, fill=primary, width=5)

        draw.text((cx, cy + 134), label.upper()[:20], font=self._font(25, True), fill=primary, anchor="ma")

    def _make_image(self, item):
        sku, name, category, pack, form_factor, container, best_for, label, price = item
        primary, accent, background = self._palette(category)
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "catalog"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._slug(sku)}.png"

        canvas = Image.new("RGB", (900, 650), background)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rounded_rectangle((28, 28, 872, 622), radius=28, fill=(255, 255, 255, 76), outline="#d9cfae", width=2)
        draw.rounded_rectangle((34, 34, 866, 140), radius=18, fill=(8, 9, 8, 224), outline="#d4af37", width=3)
        draw.text((60, 52), "GarlicShop", font=self._font(36, True), fill="#ffffff")
        draw.text((285, 60), "100% NATURAL FARM", font=self._font(18, True), fill="#d4af37")
        draw.rounded_rectangle((620, 54, 838, 118), radius=14, fill=primary)
        draw.text((729, 73), category.upper()[:18], font=self._font(17, True), fill="#ffffff", anchor="ma")

        self._draw_natural_icon(draw, (450, 312), label, primary, accent)

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
        for index, item in enumerate(RAW_FARM_CATALOG, start=1):
            sku, name, category, pack, form_factor, container, best_for, label, price = item
            image_path = self._make_image(item)
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "price": Decimal(price),
                    "image": image_path,
                    "brand": "GarlicShop Natural",
                    "stock_quantity": 50 + (index % 80),
                    "low_stock_threshold": 10,
                    "description": (
                        f"{name} - direct farm natural product, clean sorted, "
                        "fresh packed and quality checked by GarlicShop."
                    ),
                    "category": category,
                    "pack_of": pack,
                    "form_factor": form_factor,
                    "container_type": container,
                    "highlights": (
                        "Direct farm natural product\n"
                        "Clean sorted batch\n"
                        "No artificial branding confusion\n"
                        "Fresh GarlicShop packing"
                    ),
                    "harvest_date": date(2026, 7, 10),
                    "packed_date": date(2026, 7, 26),
                    "shelf_life_days": 45 if "Produce" in category or "Greens" in category else 120,
                    "aroma_level": "Natural",
                    "taste_profile": "Fresh, natural and farm selected",
                    "best_for": best_for,
                    "is_available": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"GarlicShop raw natural farm catalog ready: {len(RAW_FARM_CATALOG)} products."
        ))
