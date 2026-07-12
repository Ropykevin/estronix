"""Order and checkout forms."""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from app.utils.kenya_data import KENYA_COUNTY_CHOICES


class CheckoutForm(FlaskForm):
    full_name = StringField(
        "Full Name",
        validators=[DataRequired(message="Full name is required."), Length(max=160)],
    )
    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(message="Phone number is required."),
            Regexp(r"^(\+254|254|0)[17]\d{8}$", message="Enter a valid Kenyan phone number."),
        ],
    )
    address_line1 = StringField(
        "Address Line 1",
        validators=[DataRequired(message="Address is required."), Length(max=255)],
    )
    address_line2 = StringField("Address Line 2", validators=[Optional(), Length(max=255)])
    city = StringField(
        "City / Town",
        validators=[DataRequired(message="City or town is required."), Length(max=100)],
    )
    county = SelectField(
        "County",
        choices=[("", "Select county")] + KENYA_COUNTY_CHOICES,
        validators=[DataRequired(message="Please select a county.")],
    )
    postal_code = StringField("Postal Code", validators=[Optional(), Length(max=20)])
    customer_notes = TextAreaField("Order Notes", validators=[Optional(), Length(max=500)])
    payment_method = SelectField(
        "Payment Method",
        choices=[("mpesa", "M-Pesa"), ("cod", "Cash on Delivery")],
        validators=[DataRequired(message="Please select a payment method.")],
    )
    submit = SubmitField("Place Order")
