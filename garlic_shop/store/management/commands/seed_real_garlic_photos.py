from pathlib import Path
import json
import time
import urllib.parse
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

SEARCH_TERMS = {
    "fresh": ["garlic bulbs", "garlic cloves", "fresh garlic", "garlic harvest"],
    "peeled": ["peeled garlic cloves", "garlic cloves", "chopped garlic"],
    "powder": ["garlic powder", "dried garlic", "garlic flakes"],
    "pickle": ["pickled garlic", "garlic pickle", "garlic in jar"],
    "black": ["black garlic"],
    "sauce": ["garlic sauce", "garlic paste"],
    "oil": ["garlic oil", "garlic olive oil"],
}


class Command(BaseCommand):
    help = "Set natural real garlic photos and galleries for all available GarlicShop products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--search-commons",
            action="store_true",
            help="Try extra Wikimedia Commons searches. Off by default to avoid rate limits.",
        )

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

    def _commons_search(self, term, limit=8):
        query = urllib.parse.urlencode({
            "action": "query",
            "generator": "search",
            "gsrsearch": term,
            "gsrnamespace": "6",
            "gsrlimit": str(limit),
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": "1000",
            "format": "json",
            "formatversion": "2",
        })
        url = f"https://commons.wikimedia.org/w/api.php?{query}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GarlicShopCatalogSeeder/1.0 (local catalog images)"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        results = []
        for page in payload.get("query", {}).get("pages", []):
            info = (page.get("imageinfo") or [{}])[0]
            mime = info.get("mime", "")
            image_url = info.get("thumburl") or info.get("url")
            if image_url and mime.startswith("image/"):
                results.append((page.get("title", "image"), image_url))
        return results

    def _download_pool_image(self, group, index, title, url):
        target_dir = Path(settings.MEDIA_ROOT) / "products" / "source_pool" / group
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(char if char.isalnum() else "-" for char in title.lower()).strip("-")[:70]
        target = target_dir / f"{index:02d}-{safe_name}.jpg"
        if target.exists() and target.stat().st_size > 1000:
            return target

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GarlicShopCatalogSeeder/1.0 (local catalog images)"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            target.write_bytes(response.read())
        time.sleep(0.7)
        return target

    def _build_source_pool(self, downloaded, search_commons=False):
        pool = {key: [] for key in SEARCH_TERMS}
        for key, source in downloaded.items():
            if source:
                if key == "black":
                    pool["black"].append(source)
                elif key == "fresh":
                    pool["fresh"].append(source)

        cached_root = Path(settings.MEDIA_ROOT) / "products" / "source_pool"
        for group in pool:
            group_dir = cached_root / group
            if group_dir.exists():
                for source in sorted(group_dir.glob("*.jpg")):
                    if source.stat().st_size > 1000 and source not in pool[group]:
                        pool[group].append(source)

        if not search_commons:
            fallback = downloaded.get("fresh") or downloaded.get("black")
            if fallback:
                for group in pool:
                    if not pool[group]:
                        pool[group].append(fallback)
            return pool

        for group, terms in SEARCH_TERMS.items():
            if len(pool[group]) >= 4:
                continue
            for term in terms:
                try:
                    results = self._commons_search(term)
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f"Search failed for {term}: {exc}"))
                    continue

                for title, url in results:
                    if len(pool[group]) >= 10:
                        break
                    try:
                        source = self._download_pool_image(group, len(pool[group]) + 1, title, url)
                        Image.open(source).verify()
                        pool[group].append(source)
                    except Exception as exc:
                        self.stdout.write(self.style.WARNING(f"Image skipped for {term}: {exc}"))
                if len(pool[group]) >= 6:
                    break

        fallback = downloaded.get("fresh") or downloaded.get("black")
        if fallback:
            for group in pool:
                if not pool[group]:
                    pool[group].append(fallback)
        return pool

    def _all_sources(self, pool, fallback):
        sources = []
        for group_sources in pool.values():
            for source in group_sources:
                if source not in sources:
                    sources.append(source)
        if fallback and fallback not in sources:
            sources.append(fallback)
        return sources or [fallback]

    def _photo_key(self, product):
        text = f"{product.name} {product.category} {product.form_factor}".lower()
        if "black" in text:
            return "black"
        if "pickle" in text or "chutney" in text:
            return "pickle"
        if "sauce" in text or "mayo" in text or "paste" in text:
            return "sauce"
        if "oil" in text:
            return "oil"
        if "peeled" in text or "chopped" in text or "minced" in text:
            return "peeled"
        if "powder" in text or "flakes" in text or "granules" in text or "salt" in text:
            return "powder"
        if "seed" in text or "organic" in text:
            return "fresh"
        return "whole"

    def _crop_variant(self, source_path, product, variant, seed=0):
        output_dir = Path(settings.MEDIA_ROOT) / "products" / "multiple" / "real"
        output_dir.mkdir(parents=True, exist_ok=True)
        slug = (product.sku or f"product-{product.id}").lower().replace("/", "-")
        output = output_dir / f"{slug}-{variant}.jpg"

        image = Image.open(source_path).convert("RGB")
        if seed % 2:
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if seed % 5 in (1, 3):
            image = image.rotate((-2, 2, -1, 1)[seed % 4], resample=Image.Resampling.BICUBIC, expand=False)
        width, height = image.size
        crops = {
            "main": (0.04, 0.04, 0.96, 0.96),
            "closeup": (0.18, 0.12, 0.82, 0.82),
            "lifestyle": (0.0, 0.0, 1.0, 0.88),
            "detail": (0.1, 0.22, 0.9, 1.0),
        }
        left, top, right, bottom = crops.get(variant, crops["main"])
        shift_x = ((seed % 7) - 3) * 0.015
        shift_y = (((seed // 2) % 5) - 2) * 0.015
        left = max(0, min(0.86, left + shift_x))
        right = max(left + 0.12, min(1, right + shift_x))
        top = max(0, min(0.86, top + shift_y))
        bottom = max(top + 0.12, min(1, bottom + shift_y))
        cropped = image.crop((
            int(width * left),
            int(height * top),
            int(width * right),
            int(height * bottom),
        ))
        cropped = cropped.resize((900, 650), Image.Resampling.LANCZOS)
        cropped = ImageEnhance.Color(cropped).enhance(1.02 + ((seed % 4) * 0.03))
        cropped = ImageEnhance.Contrast(cropped).enhance(1.02 + ((seed % 3) * 0.03))
        cropped = ImageEnhance.Brightness(cropped).enhance(0.98 + ((seed % 5) * 0.015))
        cropped.save(output, quality=90)
        return output

    def _set_product_image(self, product, source_path, variant, seed):
        main_path = self._crop_variant(source_path, product, variant, seed)
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
        pool = self._build_source_pool(downloaded, search_commons=options["search_commons"])
        all_sources = self._all_sources(pool, fallback)

        products = (
            Product.objects.filter(is_available=True)
            .filter(name__icontains="garlic")
            .order_by("id")
        )

        updated = 0
        galleries = 0
        for index, product in enumerate(products):
            key = self._photo_key(product)
            source_list = pool.get(key) or []
            if len(source_list) < 2:
                source_list = all_sources
            source = source_list[(index * 3 + product.id) % len(source_list)]
            main_variant = ("main", "closeup", "lifestyle", "detail")[index % 4]
            self._set_product_image(product, source, main_variant, index + product.id)
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
            for gallery_index, variant in enumerate(("closeup", "lifestyle", "detail")):
                gallery_source = source_list[(index + gallery_index + 1) % len(source_list)]
                gallery_path = self._crop_variant(gallery_source, product, variant, index + gallery_index + product.id)
                with gallery_path.open("rb") as handle:
                    image = ProductImage(product=product)
                    image.image.save(f"real/{gallery_path.name}", File(handle), save=True)
                galleries += 1

        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated} products with real natural photos and {galleries} gallery images."
        ))
