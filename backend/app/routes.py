import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from .models import Order, OrderItem, Product, db

api = Blueprint("api", __name__, url_prefix="/api")
PHONE_PATTERN = re.compile(r"[+0-9() -]{9,20}\Z")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


def error(message, status):
    return jsonify({"error": message}), status


def parse_price_parameter(name):
    raw_value = request.args.get(name)
    if raw_value is None or raw_value == "":
        return None
    try:
        value = Decimal(raw_value)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Параметр {name} должен быть числом.")
    if not value.is_finite() or value < 0 or value > Decimal("999999999999"):
        raise ValueError(f"Параметр {name} вне допустимого диапазона.")
    return value


@api.get("/health")
def health():
    try:
        db.session.execute(select(1))
    except SQLAlchemyError:
        current_app.logger.exception("Database health check failed")
        return jsonify({"status": "unavailable"}), 503
    return jsonify({"status": "ok"})


@api.get("/categories")
def categories():
    values = db.session.execute(
        select(Product.category).distinct().order_by(Product.category.asc())
    ).scalars()
    return jsonify({"categories": list(values)})


@api.get("/products")
def products():
    statement = select(Product)
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "featured")
    if len(search) > 100 or len(category) > 60:
        return error("Поисковый запрос или категория слишком длинные.", 400)
    try:
        minimum = parse_price_parameter("min_price")
        maximum = parse_price_parameter("max_price")
    except ValueError as exc:
        return error(str(exc), 400)
    if minimum is not None and maximum is not None and minimum > maximum:
        return error("Минимальная цена не может быть больше максимальной.", 400)

    if search:
        statement = statement.where(
            Product.name.icontains(search, autoescape=True)
            | Product.specs.icontains(search, autoescape=True)
        )
    if category:
        statement = statement.where(Product.category == category)
    if minimum is not None:
        statement = statement.where(Product.price >= minimum)
    if maximum is not None:
        statement = statement.where(Product.price <= maximum)

    sort_options = {
        "featured": (Product.featured_rank.asc(), Product.id.asc()),
        "price_asc": (Product.price.asc(), Product.id.asc()),
        "price_desc": (Product.price.desc(), Product.id.asc()),
        "name_asc": (Product.name.asc(), Product.id.asc()),
    }
    if sort not in sort_options:
        return error("Неизвестный способ сортировки.", 400)
    statement = statement.order_by(*sort_options[sort])
    rows = db.session.execute(statement.limit(100)).scalars()
    return jsonify({"products": [product.to_dict() for product in rows]})


def validate_order_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Тело запроса должно быть JSON-объектом.")
    customer = payload.get("customer")
    items = payload.get("items")
    if not isinstance(customer, dict):
        raise ValueError("Укажите данные покупателя.")
    if not isinstance(items, list) or not items or len(items) > 20:
        raise ValueError("В заказе должно быть от 1 до 20 позиций.")

    name = customer.get("name")
    phone = customer.get("phone")
    email = customer.get("email")
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 100:
        raise ValueError("Имя должно содержать от 2 до 100 символов.")
    if not isinstance(phone, str) or not PHONE_PATTERN.fullmatch(phone.strip()):
        raise ValueError("Проверьте номер телефона.")
    digit_count = sum(character.isdigit() for character in phone)
    if not 9 <= digit_count <= 15:
        raise ValueError("Номер телефона должен содержать от 9 до 15 цифр.")
    if email is not None and email != "":
        if not isinstance(email, str) or len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
            raise ValueError("Проверьте адрес электронной почты.")

    normalized_items = []
    seen_product_ids = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Некорректная позиция заказа.")
        product_id = item.get("product_id")
        quantity = item.get("quantity")
        if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1:
            raise ValueError("Некорректный идентификатор товара.")
        if product_id in seen_product_ids:
            raise ValueError("Каждый товар можно указать в заказе только один раз.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 99:
            raise ValueError("Количество товара должно быть от 1 до 99.")
        normalized_items.append((product_id, quantity))
        seen_product_ids.add(product_id)
    return name.strip(), phone.strip(), email.strip() if isinstance(email, str) and email.strip() else None, normalized_items


@api.post("/orders")
def create_order():
    if not request.is_json:
        return error("Отправьте заказ в формате JSON.", 415)
    try:
        name, phone, email, requested_items = validate_order_payload(request.get_json(silent=False))
    except ValueError as exc:
        return error(str(exc), 400)

    product_ids = [product_id for product_id, _ in requested_items]
    try:
        products_by_id = {
            product.id: product
            for product in db.session.execute(
                select(Product).where(Product.id.in_(product_ids)).with_for_update()
            ).scalars()
        }
        if len(products_by_id) != len(requested_items):
            missing_ids = sorted(set(product_ids) - set(products_by_id))
            return error(f"Товар не найден (ID: {', '.join(map(str, missing_ids))}).", 404)

        order_items = []
        total = Decimal("0")
        for product_id, quantity in requested_items:
            product = products_by_id[product_id]
            line_total = product.price * quantity
            total += line_total
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

        order = Order(
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            total=total,
            items=order_items,
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"order": order.to_dict()}), 201
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Order creation failed")
        return error("Не удалось сохранить заказ. Попробуйте ещё раз.", 500)
