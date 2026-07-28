from datetime import date
from decimal import Decimal
from pathlib import Path
import re
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product


AGRI_CATALOG = [
    ("GS-WHEAT-5KG", "GarlicShop Sharbati Wheat 5kg", "Farm Grains", "5kg", "Whole Grain", "Premium Bag", "Home flour milling", "Wheat", "349.00"),
    ("GS-WHEAT-10KG", "GarlicShop Sharbati Wheat 10kg", "Farm Grains", "10kg", "Whole Grain", "Premium Bag", "Monthly ration", "Wheat", "649.00"),
    ("GS-RICE-5KG", "GarlicShop Indrayani Rice 5kg", "Farm Grains", "5kg", "Rice Grain", "Premium Bag", "Daily meals", "Rice", "499.00"),
    ("GS-RICE-BROWN-2KG", "GarlicShop Brown Rice 2kg", "Farm Grains", "2kg", "Rice Grain", "Pouch", "Healthy meals", "Rice", "229.00"),
    ("GS-JOWAR-2KG", "GarlicShop Jowar 2kg", "Millets", "2kg", "Millet Grain", "Pouch", "Bhakri", "Jowar", "179.00"),
    ("GS-BAJRA-2KG", "GarlicShop Bajra 2kg", "Millets", "2kg", "Millet Grain", "Pouch", "Winter meals", "Bajra", "169.00"),
    ("GS-RAGI-1KG", "GarlicShop Ragi 1kg", "Millets", "1kg", "Millet Grain", "Pouch", "Healthy breakfast", "Ragi", "119.00"),
    ("GS-TUR-DAL-1KG", "GarlicShop Tur Dal 1kg", "Pulses", "1kg", "Dal", "Pouch", "Dal tadka", "Tur Dal", "159.00"),
    ("GS-CHANA-DAL-1KG", "GarlicShop Chana Dal 1kg", "Pulses", "1kg", "Dal", "Pouch", "Snacks and dal", "Chana Dal", "129.00"),
    ("GS-MOONG-DAL-1KG", "GarlicShop Moong Dal 1kg", "Pulses", "1kg", "Dal", "Pouch", "Light meals", "Moong Dal", "149.00"),
    ("GS-MASOOR-DAL-1KG", "GarlicShop Masoor Dal 1kg", "Pulses", "1kg", "Dal", "Pouch", "Quick cooking", "Masoor Dal", "135.00"),
    ("GS-URAD-DAL-1KG", "GarlicShop Urad Dal 1kg", "Pulses", "1kg", "Dal", "Pouch", "Idli and dal", "Urad Dal", "169.00"),
    ("GS-KABULI-CHANA-1KG", "GarlicShop Kabuli Chana 1kg", "Pulses", "1kg", "Whole Pulse", "Pouch", "Chole", "Kabuli Chana", "179.00"),
    ("GS-RAJMA-1KG", "GarlicShop Rajma 1kg", "Pulses", "1kg", "Whole Bean", "Pouch", "Rajma curry", "Rajma", "189.00"),
    ("GS-SOYBEAN-1KG", "GarlicShop Soybean 1kg", "Oil Seeds", "1kg", "Bean", "Pouch", "Protein meals", "Soybean", "119.00"),
    ("GS-GROUNDNUT-1KG", "GarlicShop Groundnut 1kg", "Oil Seeds", "1kg", "Nut", "Pouch", "Chutney and snacks", "Groundnut", "169.00"),
    ("GS-SESAME-500", "GarlicShop Sesame Seeds 500g", "Oil Seeds", "500g", "Seeds", "Jar", "Laddu and garnish", "Sesame", "149.00"),
    ("GS-FLAX-500", "GarlicShop Flax Seeds 500g", "Oil Seeds", "500g", "Seeds", "Jar", "Health mix", "Flax", "159.00"),
    ("GS-MUSTARD-500", "GarlicShop Mustard Seeds 500g", "Spices", "500g", "Seeds", "Jar", "Pickle tempering", "Mustard", "99.00"),
    ("GS-CUMIN-250", "GarlicShop Cumin Seeds 250g", "Spices", "250g", "Seeds", "Jar", "Tadka", "Cumin", "149.00"),
    ("GS-CORIANDER-500", "GarlicShop Coriander Seeds 500g", "Spices", "500g", "Seeds", "Jar", "Masala grinding", "Coriander", "119.00"),
    ("GS-TURMERIC-250", "GarlicShop Turmeric Powder 250g", "Spices", "250g", "Powder", "Jar", "Daily cooking", "Turmeric", "129.00"),
    ("GS-CHILLI-250", "GarlicShop Red Chilli Powder 250g", "Spices", "250g", "Powder", "Jar", "Spicy cooking", "Red Chilli", "139.00"),
    ("GS-CORIANDER-POWDER-250", "GarlicShop Coriander Powder 250g", "Spices", "250g", "Powder", "Jar", "Curries", "Coriander Powder", "99.00"),
    ("GS-ONION-2KG", "GarlicShop Fresh Onion 2kg", "Fresh Vegetables", "2kg", "Whole Bulbs", "Mesh Bag", "Daily cooking", "Onion", "89.00"),
    ("GS-POTATO-2KG", "GarlicShop Fresh Potato 2kg", "Fresh Vegetables", "2kg", "Whole Tubers", "Mesh Bag", "Daily meals", "Potato", "79.00"),
    ("GS-GINGER-250", "GarlicShop Fresh Ginger 250g", "Fresh Vegetables", "250g", "Rhizome", "Fresh Pack", "Tea and curry", "Ginger", "69.00"),
    ("GS-GREEN-CHILLI-250", "GarlicShop Green Chilli 250g", "Fresh Vegetables", "250g", "Fresh Chilli", "Fresh Pack", "Spicy cooking", "Green Chilli", "49.00"),
    ("GS-LEMON-500", "GarlicShop Farm Lemon 500g", "Fresh Vegetables", "500g", "Fresh Citrus", "Fresh Pack", "Pickle and drinks", "Lemon", "59.00"),
    ("GS-CURRY-LEAVES-100", "GarlicShop Curry Leaves 100g", "Fresh Herbs", "100g", "Leaves", "Fresh Pack", "Tadka", "Curry Leaves", "39.00"),
    ("GS-METHI-SEED-250", "GarlicShop Methi Seeds 250g", "Spices", "250g", "Seeds", "Jar", "Pickle and sprouts", "Methi", "79.00"),
    ("GS-AJWAIN-250", "GarlicShop Ajwain 250g", "Spices", "250g", "Seeds", "Jar", "Digestive spice", "Ajwain", "119.00"),
    ("GS-JAGGERY-1KG", "GarlicShop Desi Jaggery 1kg", "Farm Sweeteners", "1kg", "Blocks", "Box", "Tea and sweets", "Jaggery", "129.00"),
    ("GS-JAGGERY-POWDER-500", "GarlicShop Jaggery Powder 500g", "Farm Sweeteners", "500g", "Powder", "Pouch", "Healthy sweetener", "Jaggery Powder", "99.00"),
    ("GS-HONEY-500", "GarlicShop Farm Honey 500g", "Farm Sweeteners", "500g", "Honey", "Glass Jar", "Daily wellness", "Honey", "249.00"),
    ("GS-COW-GHEE-500", "GarlicShop Farm Ghee 500ml", "Farm Dairy", "500ml", "Ghee", "Jar", "Cooking and sweets", "Ghee", "399.00"),
    ("GS-VERMI-5KG", "GarlicShop Vermicompost 5kg", "Farm Supplies", "5kg", "Compost", "Bag", "Kitchen garden", "Vermicompost", "199.00"),
    ("GS-NEEM-CAKE-5KG", "GarlicShop Neem Cake 5kg", "Farm Supplies", "5kg", "Soil Additive", "Bag", "Organic farming", "Neem Cake", "299.00"),
    ("GS-SEED-MIX-500", "GarlicShop Kitchen Garden Seed Mix", "Farm Seeds", "500g", "Mixed Seeds", "Pouch", "Home garden", "Seed Mix", "149.00"),
    ("GS-CORIANDER-SEED-250", "GarlicShop Coriander Seed Pack 250g", "Farm Seeds", "250g", "Seeds", "Pouch", "Kitchen garden", "Coriander Seed", "69.00"),
]


class Command(BaseCommand):
    help = "Create agriculture-related GarlicShop products with branded local images."

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
            "Farm Grains": ("#7a4e18", "#f2d28a", "#fff8e1"),
            "Millets": ("#6a5424", "#d9b44a", "#fbf3d0"),
            "Pulses": ("#8a5a16", "#f2b84b", "#fff2cf"),
            "Oil Seeds": ("#4f5f27", "#b7c65b", "#eef5cf"),
            "Spices": ("#8d2f18", "#e08828", "#fff0d9"),
            "Fresh Vegetables": ("#1f6b39", "#73b45a", "#edf8e8"),
            "Fresh Herbs": ("#1d6a48", "#6fbf7a", "#eaf8ee"),
            "Farm Sweeteners": ("#6b421c", "#d79b3a", "#fff2d4"),
            "Farm Dairy": ("#7a611e", "#f1cf67", "#fff8dc"),
            "Farm Supplies": ("#31542a", "#86a85d", "#eef5e6"),
            "Farm Seeds": ("#335b31", "#9bbd57", "#f2f8dd"),
        }
        return palettes.get(category, ("#226439", "#d4af37", "#f7f8f3"))

    def _draw_crop_icon(self, draw, center, label, primary, accent):
        cx, cy = center
        draw.ellipse((cx - 130, cy - 105, cx + 130, cy + 105), fill=(255, 255, 255, 224), outline=accent, width=6)
        for offset in (-72, -36, 0, 36, 72):
            draw.ellipse((cx + offset - 20, cy - 42, cx + offset + 20, cy + 42), fill=accent)
            draw.line((cx + offset, cy + 44, cx + offset, cy + 78), fill=primary, width=5)
        draw.arc((cx - 96, cy - 78, cx + 96, cy + 96), 15, 165, fill=primary, width=5)
        draw.text((cx, cy + 118), label.upper()[:18], font=self._font(26, True), fill=primary, anchor="ma")

    def _make_image(self, item):
        sku, name, category, pack, form_factor, container, best_for, label, price = item
        primary, accent, background = self._palette(category)
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "catalog"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self._slug(sku)}.png"

        canvas = Image.new("RGB", (900, 650), background)
        draw = ImageDraw.Draw(canvas, "RGBA")

        for radius, opacity in ((470, 20), (360, 28), (250, 36)):
            draw.ellipse((450 - radius, 180 - radius, 450 + radius, 180 + radius), fill=(*Image.new("RGB", (1, 1), accent).getpixel((0, 0)), opacity))

        draw.rounded_rectangle((34, 34, 866, 140), radius=18, fill=(8, 9, 8, 222), outline="#d4af37", width=3)
        draw.text((60, 52), "GarlicShop", font=self._font(36, True), fill="#ffffff")
        draw.text((285, 60), "FARM ESSENTIALS", font=self._font(18, True), fill="#d4af37")
        draw.rounded_rectangle((630, 54, 838, 118), radius=14, fill=primary)
        draw.text((734, 73), category.upper()[:18], font=self._font(17, True), fill="#ffffff", anchor="ma")

        self._draw_crop_icon(draw, (450, 310), label, primary, accent)

        draw.rounded_rectangle((54, 472, 846, 614), radius=22, fill=(255, 255, 255, 235), outline="#d4af37", width=3)
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
        for index, item in enumerate(AGRI_CATALOG, start=1):
            sku, name, category, pack, form_factor, container, best_for, label, price = item
            image_path = self._make_image(item)
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "price": Decimal(price),
                    "image": image_path,
                    "brand": "GarlicShop",
                    "stock_quantity": 40 + (index % 65),
                    "low_stock_threshold": 10,
                    "description": (
                        f"{name} - GarlicShop farm selected {category.lower()} product "
                        "with clean packing, reliable sourcing, and quality checked batch."
                    ),
                    "category": category,
                    "pack_of": pack,
                    "form_factor": form_factor,
                    "container_type": container,
                    "highlights": (
                        "GarlicShop farm essentials pack\n"
                        "Reliable farmer sourcing\n"
                        "Quality checked batch\n"
                        "Clean premium packing"
                    ),
                    "harvest_date": date(2026, 7, 5),
                    "packed_date": date(2026, 7, 20),
                    "shelf_life_days": 120,
                    "aroma_level": "Fresh" if "Fresh" in category else "Medium",
                    "taste_profile": "Farm fresh, clean and natural",
                    "best_for": best_for,
                    "is_available": True,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"GarlicShop agriculture catalog ready: {len(AGRI_CATALOG)} products."
        ))
