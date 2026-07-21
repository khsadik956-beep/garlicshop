from pathlib import Path
import re
import textwrap

from django.conf import settings
from django.core.management.base import BaseCommand

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from store.models import Product, ProductImage


class Command(BaseCommand):
    help = "Generate 3 related GarlicShop gallery images for every available product."

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
        return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "product"

    def _category_color(self, product):
        colors = {
            "fresh": "#226439",
            "organic": "#2f7d32",
            "powder": "#b8860b",
            "seasoning": "#8a6115",
            "pickle": "#8f2f16",
            "chutney": "#a14612",
            "oil": "#7d681c",
            "sauce": "#7b1f1f",
            "spread": "#6b5724",
            "bulk": "#143d24",
            "seed": "#31542a",
            "combo": "#1f1f1f",
        }
        key = f"{product.category} {product.form_factor}".lower()
        for token, color in colors.items():
            if token in key:
                return color
        return "#226439"

    def _source_path(self, product):
        if product.image:
            candidate = Path(settings.MEDIA_ROOT) / str(product.image)
            if candidate.exists():
                return candidate

        fallback_map = [
            ("powder", "powder.png"),
            ("pickle", "pickle.png"),
            ("chutney", "powder.png"),
            ("sauce", "pickle.png"),
            ("oil", "offer-garlic.png"),
            ("combo", "offer-garlic.png"),
            ("bulk", "offer-garlic.png"),
            ("peeled", "pickle.png"),
        ]
        key = f"{product.category} {product.form_factor} {product.name}".lower()
        for token, filename in fallback_map:
            if token in key:
                return Path(settings.BASE_DIR).parent / "static" / "images" / filename
        return Path(settings.BASE_DIR).parent / "static" / "images" / "whole-garlic.png"

    def _base_canvas(self, product):
        source = self._source_path(product)
        image = Image.open(source).convert("RGB")
        image.thumbnail((820, 560), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (900, 650), "#f7f8f3")
        x = (900 - image.width) // 2
        y = (650 - image.height) // 2
        canvas.paste(image, (x, y))
        return canvas.filter(ImageFilter.UnsharpMask(radius=1, percent=115, threshold=3))

    def _wrapped_text(self, draw, text, box, font, fill):
        x, y, width, line_height = box
        for index, line in enumerate(textwrap.wrap(text, width=width)[:2]):
            draw.text((x, y + index * line_height), line, font=font, fill=fill)

    def _make_gallery_image(self, product, variant):
        slug = self._slug(product.sku or product.name)
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "multiple" / "catalog"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{slug}-{variant}.png"

        canvas = self._base_canvas(product)
        draw = ImageDraw.Draw(canvas, "RGBA")
        accent = self._category_color(product)

        if variant == "pack":
            draw.rounded_rectangle((34, 34, 866, 136), radius=20, fill=(8, 9, 8, 218), outline="#d4af37", width=3)
            draw.text((62, 52), "GarlicShop", font=self._font(38, True), fill="#ffffff")
            draw.text((310, 61), "PACK SHOT", font=self._font(18, True), fill="#d4af37")
            draw.rounded_rectangle((620, 52, 838, 116), radius=14, fill=accent)
            draw.text((729, 71), (product.pack_of or "Fresh Pack").upper()[:18], font=self._font(18, True), fill="#ffffff", anchor="ma")
            draw.rounded_rectangle((54, 472, 846, 610), radius=22, fill=(255, 255, 255, 232), outline="#d4af37", width=3)
            self._wrapped_text(draw, product.name.replace("GarlicShop ", ""), (84, 492, 28, 38), self._font(34, True), "#111111")
            draw.text((84, 570), f"{product.category} | {product.form_factor}", font=self._font(19, True), fill=accent)

        elif variant == "closeup":
            overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle((0, 0, 900, 650), fill=(0, 0, 0, 70))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(canvas, "RGBA")
            draw.ellipse((62, 72, 360, 370), outline="#d4af37", width=8, fill=(255, 255, 255, 38))
            draw.rounded_rectangle((390, 92, 840, 290), radius=24, fill=(255, 255, 255, 232), outline="#d4af37", width=3)
            draw.text((420, 120), "QUALITY CLOSE-UP", font=self._font(28, True), fill="#111111")
            draw.text((420, 172), f"Aroma: {product.aroma_level}", font=self._font(23, True), fill=accent)
            draw.text((420, 214), product.taste_profile or "Fresh and bold", font=self._font(19), fill="#444444")
            draw.rounded_rectangle((390, 320, 840, 405), radius=18, fill=(8, 9, 8, 218))
            draw.text((420, 346), "Farm selected | Freshness checked", font=self._font(23, True), fill="#d4af37")

        else:
            draw.rounded_rectangle((42, 42, 858, 598), radius=28, fill=(255, 255, 255, 34), outline="#d4af37", width=4)
            draw.rounded_rectangle((78, 72, 430, 178), radius=20, fill=(8, 9, 8, 225))
            draw.text((106, 94), "GarlicShop", font=self._font(34, True), fill="#ffffff")
            draw.text((106, 134), "LIFESTYLE USE", font=self._font(18, True), fill="#d4af37")
            draw.rounded_rectangle((86, 426, 812, 574), radius=24, fill=(255, 255, 255, 232), outline="#d4af37", width=3)
            draw.text((118, 450), "Best For", font=self._font(23, True), fill=accent)
            self._wrapped_text(draw, product.best_for or "Daily cooking", (118, 488, 34, 34), self._font(31, True), "#111111")
            draw.text((650, 458), f"Rs. {product.price}", font=self._font(31, True), fill="#111111")
            draw.text((650, 504), "Premium Pack", font=self._font(19, True), fill=accent)

        canvas.save(output_path, quality=92)
        return f"products/multiple/catalog/{output_path.name}"

    def handle(self, *args, **options):
        products = Product.objects.filter(is_available=True).order_by("id")
        created = 0
        for product in products:
            ProductImage.objects.filter(
                product=product,
                image__startswith="products/multiple/catalog/",
            ).delete()
            for variant in ("pack", "closeup", "lifestyle"):
                image_path = self._make_gallery_image(product, variant)
                ProductImage.objects.create(product=product, image=image_path)
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Generated {created} gallery images for {products.count()} products."
        ))
