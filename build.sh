#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python garlic_shop/manage.py collectstatic --no-input
python garlic_shop/manage.py migrate

if [ "$AUTO_SEED_CATALOG" = "True" ]; then
    python garlic_shop/manage.py seed_50_products
    python garlic_shop/manage.py seed_agri_products
    python garlic_shop/manage.py seed_product_galleries
fi
