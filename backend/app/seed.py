from decimal import Decimal

from .models import Product, db

PRODUCTS = [
    {
        "name": "ASUS Vivobook 15",
        "category": "Для учёбы",
        "specs": "15.6″ FHD · Intel Core i5 · 16 ГБ · 512 ГБ SSD",
        "description": "Универсальный ноутбук для учёбы, видеозвонков и повседневной работы. Лёгкий корпус и быстрый SSD помогают сосредоточиться на главном.",
        "price": 7499000,
        "badge": "ВЫБОР ПОКУПАТЕЛЕЙ",
        "featured_rank": 1,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "Apple MacBook Air 13",
        "category": "Для работы",
        "specs": "13.6″ Retina · Apple M3 · 16 ГБ · 512 ГБ SSD",
        "description": "Тонкий и лёгкий ноутбук с ярким дисплеем и тихой работой. Подойдёт для мобильной работы, общения и творческих проектов.",
        "price": 15999000,
        "badge": "ЛЁГКИЙ ВЫБОР",
        "featured_rank": 2,
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "Lenovo IdeaPad Slim 5",
        "category": "Для учёбы",
        "specs": "14″ WUXGA · AMD Ryzen 7 · 16 ГБ · 1 ТБ SSD",
        "description": "Сбалансированная конфигурация для многозадачности, учёбы и поездок. Удобная клавиатура и запас памяти на проекты и документы.",
        "price": 9999000,
        "badge": "УМНЫЙ БАЛАНС",
        "featured_rank": 3,
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "HP Pavilion Plus 14",
        "category": "Для творчества",
        "specs": "14″ 2.8K OLED · Intel Core Ultra 5 · 16 ГБ · 512 ГБ SSD",
        "description": "Детализированный OLED-экран и отзывчивая платформа для дизайна, контента и продуктивной работы каждый день.",
        "price": 12499000,
        "badge": "ЯРКИЙ ДИСПЛЕЙ",
        "featured_rank": 4,
        "image_url": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "Acer Aspire 5",
        "category": "Для работы",
        "specs": "15.6″ FHD · Intel Core i5 · 16 ГБ · 512 ГБ SSD",
        "description": "Практичный ноутбук для документов, браузера и онлайн-встреч. Достаточно мощности для рабочих задач без переплаты.",
        "price": 6999000,
        "badge": "ПРАКТИЧНЫЙ",
        "featured_rank": 5,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "MSI Thin 15",
        "category": "Для игр",
        "specs": "15.6″ 144 Гц · Intel Core i7 · 16 ГБ · RTX 4060",
        "description": "Игровая видеокарта, дисплей с высокой частотой обновления и производительная платформа для игр и графических задач.",
        "price": 14999000,
        "badge": "БОЛЬШЕ МОЩНОСТИ",
        "featured_rank": 6,
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "Dell Inspiron 14",
        "category": "Для работы",
        "specs": "14″ FHD+ · Intel Core i5 · 16 ГБ · 512 ГБ SSD",
        "description": "Компактный формат для гибридной работы и поездок. Большой тачпад, удобный экран и быстрая загрузка системы.",
        "price": 8999000,
        "badge": "НА КАЖДЫЙ ДЕНЬ",
        "featured_rank": 7,
        "image_url": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=85",
    },
    {
        "name": "ASUS ROG Zephyrus G14",
        "category": "Для игр",
        "specs": "14″ 120 Гц · AMD Ryzen 9 · 32 ГБ · RTX 4070",
        "description": "Высокая производительность в компактном корпусе. Подойдёт для современных игр, монтажа видео и ресурсоёмких задач.",
        "price": 24999000,
        "badge": "МОЩНОСТЬ В ДЕТАЛЯХ",
        "featured_rank": 8,
        "image_url": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=85",
    },
]


def seed_products():
    if Product.query.first():
        return False

    for data in PRODUCTS:
        product_data = {**data, "price": Decimal(data["price"])}
        db.session.add(Product(**product_data))
    db.session.commit()
    return True
