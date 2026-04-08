# app/forms/admin.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional

class VariantForm(FlaskForm):
    sku = StringField('SKU', validators=[DataRequired()])
    size = StringField('Size', validators=[Optional()])
    color = StringField('Color', validators=[Optional()])
    color_code = StringField('Color Code (hex)', validators=[Optional()])
    price_adjustment = FloatField('Price Adjustment', default=0.0)
    stock = IntegerField('Stock', default=0)
    image_url = StringField('Image URL', validators=[Optional()])
    is_active = BooleanField('Active', default=True)