"""Trade-in forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models.tradein import DeviceCondition


class TradeInForm(FlaskForm):
    device_brand = StringField("Brand", validators=[DataRequired(), Length(max=100)])
    device_model = StringField("Model", validators=[DataRequired(), Length(max=200)])
    device_type = SelectField(
        "Device Type",
        choices=[("smartphone", "Smartphone"), ("laptop", "Laptop"), ("tablet", "Tablet"), ("default", "Other")],
        validators=[DataRequired()],
    )
    condition = SelectField(
        "Condition",
        choices=[(c.value, c.value.title()) for c in DeviceCondition],
        validators=[DataRequired()],
    )
    condition_notes = TextAreaField("Condition Details", validators=[Optional(), Length(max=500)])
    images = MultipleFileField("Device Photos", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"])])
    submit = SubmitField("Get Estimate")
