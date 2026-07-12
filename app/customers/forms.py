"""Customer account forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp

from app.utils.kenya_data import KENYA_COUNTY_CHOICES


class ProfileForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=80)])
    phone = StringField(
        "Phone",
        validators=[
            Optional(),
            Regexp(r"^(\+254|254|0)[17]\d{8}$", message="Enter a valid Kenyan phone number."),
        ],
    )
    profile_image = FileField(
        "Profile Photo",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Images only (jpg, png, gif, webp)."),
        ],
    )
    remove_profile_image = BooleanField("Remove current photo")
    submit = SubmitField("Update Profile")


class AddressForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=50)], default="Home")
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    phone = StringField(
        "Phone",
        validators=[
            DataRequired(),
            Regexp(r"^(\+254|254|0)[17]\d{8}$", message="Enter a valid Kenyan phone number."),
        ],
    )
    address_line1 = StringField("Address Line 1", validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField("Address Line 2", validators=[Length(max=255)])
    city = StringField("City", validators=[DataRequired(), Length(max=100)])
    county = SelectField(
        "County",
        choices=[("", "Select county")] + KENYA_COUNTY_CHOICES,
        validators=[DataRequired(message="Please select a county.")],
    )
    postal_code = StringField("Postal Code", validators=[Length(max=20)])
    is_default = BooleanField("Set as default address")
    submit = SubmitField("Save Address")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("new_password")],
    )
    submit = SubmitField("Change Password")


class WarrantyRegisterForm(FlaskForm):
    product_id = SelectField("Product", coerce=int, validators=[DataRequired()])
    serial_number = StringField("Serial Number", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Register Warranty")


class RepairForm(FlaskForm):
    product_name = StringField("Product Name", validators=[DataRequired(), Length(max=200)])
    brand = StringField("Brand", validators=[Optional(), Length(max=100)])
    serial_number = StringField("Serial Number", validators=[Optional(), Length(max=100)])
    issue_description = TextAreaField("Issue Description", validators=[DataRequired(), Length(min=20, max=2000)])
    submit = SubmitField("Submit Repair Request")
