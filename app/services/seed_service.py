"""Database seed service for development and demo."""

from decimal import Decimal

from app.extensions import db
from app.models import Category, Product, ProductImage, ProductSpecification, ProductStatus


class SeedService:
    """Seed sample categories and products."""

    CATEGORIES = [
        {"name": "Electronics", "children": ["Smartphones", "Laptops", "Accessories", "Home Appliances"]},
    ]

    PRODUCTS = [
        {
            "name": "Samsung Galaxy S24 Ultra",
            "sku": "SAM-S24U-256",
            "brand": "Samsung",
            "price": Decimal("149999.00"),
            "discount_price": Decimal("139999.00"),
            "stock": 25,
            "category": "Smartphones",
            "warranty": "1 Year Manufacturer Warranty",
            "featured": True,
            "specs": [("Display", "6.8\" Dynamic AMOLED"), ("RAM", "12GB"), ("Storage", "256GB"), ("Battery", "5000mAh")],
        },
        {
            "name": "iPhone 15 Pro Max",
            "sku": "APL-IP15PM-256",
            "brand": "Apple",
            "price": Decimal("189999.00"),
            "stock": 15,
            "category": "Smartphones",
            "warranty": "1 Year Apple Warranty",
            "featured": True,
            "specs": [("Display", "6.7\" Super Retina XDR"), ("Chip", "A17 Pro"), ("Storage", "256GB")],
        },
        {
            "name": "MacBook Pro 14\" M3",
            "sku": "APL-MBP14-M3",
            "brand": "Apple",
            "price": Decimal("249999.00"),
            "discount_price": Decimal("239999.00"),
            "stock": 10,
            "category": "Laptops",
            "warranty": "1 Year Apple Warranty",
            "featured": True,
            "specs": [("Chip", "Apple M3"), ("RAM", "16GB"), ("Storage", "512GB SSD"), ("Display", "14.2\" Liquid Retina XDR")],
        },
        {
            "name": "Dell XPS 15",
            "sku": "DEL-XPS15-2024",
            "brand": "Dell",
            "price": Decimal("179999.00"),
            "stock": 8,
            "category": "Laptops",
            "warranty": "2 Year Dell Warranty",
            "specs": [("Processor", "Intel Core i7"), ("RAM", "16GB"), ("Storage", "512GB SSD")],
        },
        {
            "name": "Sony WH-1000XM5",
            "sku": "SNY-WH1000XM5",
            "brand": "Sony",
            "price": Decimal("34999.00"),
            "discount_price": Decimal("29999.00"),
            "stock": 40,
            "category": "Accessories",
            "warranty": "1 Year Warranty",
            "featured": True,
            "specs": [("Type", "Over-ear"), ("Noise Cancelling", "Yes"), ("Battery", "30 hours")],
        },
        {
            "name": "Samsung 55\" QLED TV",
            "sku": "SAM-QLED55-2024",
            "brand": "Samsung",
            "price": Decimal("89999.00"),
            "stock": 12,
            "category": "Home Appliances",
            "warranty": "2 Year Warranty",
            "specs": [("Size", "55 inch"), ("Resolution", "4K UHD"), ("Smart TV", "Tizen OS")],
        },
        {
            "name": "Anker PowerCore 20000mAh",
            "sku": "ANK-PC20K",
            "brand": "Anker",
            "price": Decimal("4999.00"),
            "stock": 100,
            "category": "Accessories",
            "warranty": "18 Month Warranty",
            "specs": [("Capacity", "20000mAh"), ("Ports", "2 USB-A, 1 USB-C"), ("Fast Charge", "18W")],
        },
        {
            "name": "LG Front Load Washing Machine",
            "sku": "LG-FLWM-9KG",
            "brand": "LG",
            "price": Decimal("64999.00"),
            "stock": 6,
            "category": "Home Appliances",
            "warranty": "2 Year Warranty",
            "specs": [("Capacity", "9 kg"), ("Energy Rating", "A+++"), ("Spin Speed", "1400 RPM")],
        },
    ]

    @classmethod
    def seed_all(cls):
        cls._seed_categories()
        cls._seed_products()

    @classmethod
    def _seed_categories(cls):
        for cat_data in cls.CATEGORIES:
            parent = Category.query.filter_by(name=cat_data["name"]).first()
            if not parent:
                parent = Category(
                    name=cat_data["name"],
                    slug=Category.generate_slug(cat_data["name"]),
                    description=f"Shop {cat_data['name']} at Estronix",
                )
                db.session.add(parent)
                db.session.flush()

            for i, child_name in enumerate(cat_data.get("children", [])):
                if not Category.query.filter_by(name=child_name).first():
                    child = Category(
                        name=child_name,
                        slug=Category.generate_slug(child_name),
                        parent_id=parent.id,
                        sort_order=i,
                    )
                    db.session.add(child)

        db.session.commit()

    @classmethod
    def _seed_products(cls):
        for pdata in cls.PRODUCTS:
            if Product.query.filter_by(sku=pdata["sku"]).first():
                continue

            category = Category.query.filter_by(name=pdata["category"]).first()
            if not category:
                continue

            product = Product(
                name=pdata["name"],
                slug=Product.generate_slug(pdata["name"]),
                sku=pdata["sku"],
                brand=pdata["brand"],
                description=f"Premium {pdata['name']} available at Estronix with fast delivery across Kenya.",
                price=pdata["price"],
                discount_price=pdata.get("discount_price"),
                stock_quantity=pdata["stock"],
                warranty_info=pdata.get("warranty"),
                category_id=category.id,
                is_featured=pdata.get("featured", False),
                meta_title=f"{pdata['name']} - Buy Online | Estronix",
                meta_description=f"Buy {pdata['name']} at the best price in Kenya. {pdata.get('warranty', '')} Free delivery on orders over KES 50,000.",
            )
            db.session.add(product)
            db.session.flush()

            db.session.add(
                ProductImage(
                    product_id=product.id,
                    image_url="/static/images/placeholder-product.svg",
                    alt_text=product.name,
                    is_primary=True,
                )
            )

            for i, (key, value) in enumerate(pdata.get("specs", [])):
                db.session.add(
                    ProductSpecification(product_id=product.id, spec_key=key, spec_value=value, sort_order=i)
                )

        db.session.commit()
