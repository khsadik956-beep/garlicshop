from pathlib import Path
import time
import urllib.request

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from PIL import Image, ImageEnhance

from store.models import Product, ProductImage


IMAGE_SOURCES = {
    "fresh": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Garlic_bulbs.jpg/1024px-Garlic_bulbs.jpg"
    ),
    "black": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Black_garlic.jpg/1024px-Black_garlic.jpg"
    ),
    "botanical": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Allium_sativum_Woodwill_1793.jpg/800px-Allium_sativum_Woodwill_1793.jpg"
    ),
}


class Command(BaseCommand):
    help = "Set natural real garlic photos and galleries for all available GarlicShop products."

    def _download_image(self, key, url):
        target_dir = Path(settings.MEDIA_ROOT) / "products" / "real"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{key}.jpg"
        if target.exists() and target.stat().st_size > 1000:
            return target

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GarlicShopCatalogSeeder/1.0 (local catalog images)"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
        time.sleep(1)
        return target

    def _photo_key(self, product):
        text = f"{product.name} {product.category} {product.form_factor}".lower()
        if "black" in text:
            return "black"
        if "pickle" in text or "chutney" in text:
            return "pickle"
        if "sauce" in text or "mayo" in text or "paste" in text:
            return "sauce"
        if "peeled" in text or "chopped" in text or "minced" in text:
            return "peeled"
        if "powder" in text or "flakes" in text or "granules" in text or "salt" in text:
            return "cloves"
        if "seed" in text or "organic" in text:
            return "fresh"
        return "whole"

    def _crop_variant(self, source_path, product, variant):
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "multiple" / "real"
        output_dir.mkdir(parents=True, exist_ok=True)
        slug = (product.sku or f"product-{product.id}").lower().replace("/", "-")
        output = output_dir / f"{slug}-{variant}.jpg"

        image = Image.open(source_path).convert("RGB")
        width, height = image.size
        crops = {
            "main": (0.04, 0.04, 0.96, 0.96),
            "closeup": (0.18, 0.12, 0.82, 0.82),
            "lifestyle": (0.0, 0.0, 1.0, 0.88),
            "detail": (0.1, 0.22, 0.9, 1.0),
        }
        left, top, right, bottom = crops.get(variant, crops["main"])
        cropped = image.crop((
            int(width * left),
            int(height * top),
            int(width * right),
            int(height * bottom),
        ))
        cropped = cropped.resize((900, 650), Image.Resampling.LANCZOS)
        cropped = ImageEnhance.Color(cropped).enhance(1.08)
        cropped = ImageEnhance.Contrast(cropped).enhance(1.06)
        cropped.save(output, quality=90)
        return output

    def _set_product_image(self, product, source_path):
        main_path = self._crop_variant(source_path, product, "main")
        with main_path.open("rb") as handle:
            product.image.save(f"real/{main_path.name}", File(handle), save=False)

    def handle(self, *args, **options):
        downloaded = {}
        for key, url in IMAGE_SOURCES.items():
            try:
                downloaded[key] = self._download_image(key, url)
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Could not download {key}: {exc}"))

        fallback = downloaded.get("whole") or downloaded.get("fresh") or downloaded.get("black")
        if not fallback:
            fallback = Path(settings.BASE_DIR).parent / "static" / "images" / "whole-garlic.png"

        products = (
            Product.objects.filter(is_available=True)
            .filter(name__icontains="garlic")
            .order_by("id")
        )

        updated = 0
        galleries = 0
        for product in products:
            source = downloaded.get(self._photo_key(product), fallback)
            self._set_product_image(product, source)
            product.brand = "GarlicShop Natural"
            product.description = (
                f"{product.name} - natural GarlicShop product with real garlic photo, "
                "fresh batch quality, clean packing, and order tracking support."
            )
            product.highlights = (
                "Natural real garlic photo\n"
                "Fresh batch selected\n"
                "Clean GarlicShop packing\n"
                "Quality checked before dispatch"
            )
            product.save()
            updated += 1

            ProductImage.objects.filter(product=product).delete()
            for variant in ("closeup", "lifestyle", "detail"):
                gallery_path = self._crop_variant(source, product, variant)
                with gallery_path.open("rb") as handle:
                    image = ProductImage(product=product)
                    image.image.save(f"real/{gallery_path.name}", File(handle), save=True)
                galleries += 1

        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated} products with real natural photos and {galleries} gallery images."
        ))
