"""Admin panel forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, MultipleFileField
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.models import Product
from app.models.product import ProductStatus


class ProductForm(FlaskForm):
    def __init__(self, *args, product_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_id = product_id

    name = StringField("Product Name", validators=[DataRequired(), Length(max=200)])
    sku = StringField("SKU", validators=[DataRequired(), Length(max=50)])
    brand = StringField("Brand", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description")
    price = DecimalField("Price (KES)", validators=[DataRequired(), NumberRange(min=0)])
    discount_price = DecimalField("Discount Price", validators=[Optional(), NumberRange(min=0)])
    stock_quantity = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0)])
    warranty_info = StringField("Warranty", validators=[Length(max=255)])
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    status = SelectField(
        "Status",
        choices=[(s.value, s.value.replace("_", " ").title()) for s in ProductStatus],
        validators=[DataRequired()],
    )
    is_featured = BooleanField("Featured Product")
    meta_title = StringField("Meta Title", validators=[Length(max=200)])
    meta_description = StringField("Meta Description", validators=[Length(max=320)])
    images = MultipleFileField(
        "Product Images",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Images only (jpg, png, gif, webp)."),
        ],
    )
    submit = SubmitField("Save Product")

    def validate_sku(self, field):
        sku = field.data.upper().strip()
        query = Product.query.filter_by(sku=sku)
        if self.product_id:
            query = query.filter(Product.id != self.product_id)
        if query.first():
            raise ValidationError(f"SKU '{sku}' is already in use. Choose a unique SKU.")

    def validate_name(self, field):
        slug = Product.generate_slug(field.data)
        query = Product.query.filter_by(slug=slug)
        if self.product_id:
            query = query.filter(Product.id != self.product_id)
        if query.first():
            raise ValidationError(
                f"A product with a similar name already exists (URL: /products/{slug}). "
                "Use a more distinct name."
            )


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description")
    parent_id = SelectField("Parent Category", coerce=int, validators=[Optional()])
    sort_order = IntegerField("Sort Order", default=0)
    is_active = BooleanField("Active", default=True)
    image = FileField("Category Image", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"])])
    submit = SubmitField("Save Category")


class OrderStatusForm(FlaskForm):
    status = SelectField("Status", validators=[DataRequired()])
    tracking_number = StringField("Tracking Number", validators=[Length(max=100)])
    admin_notes = TextAreaField("Admin Notes")
    submit = SubmitField("Update Order")


class StockUpdateForm(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=0)])
    operation = SelectField(
        "Operation",
        choices=[("set", "Set Stock"), ("add", "Add Stock"), ("subtract", "Subtract Stock")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Stock")
