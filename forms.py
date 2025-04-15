from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField, IntegerField, FieldList, FormField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class SplitPaymentForm(FlaskForm):
    user_id = IntegerField("User ID", validators=[DataRequired()])
    amount_paid = FloatField("Amount Paid", validators=[DataRequired(), NumberRange(min=0)])

class ExpenseForm(FlaskForm):
    amount = FloatField("Amount", validators=[DataRequired()])
    category = SelectField("Category", choices=[
        ("Food", "Food"), 
        ("Transport", "Transport"), 
        ("Shopping", "Shopping"),
        ("Accommodation", "Accommodation"),
        ("Entertainment", "Entertainment"),
        ("Other", "Other")
    ], validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()], format='%Y-%m-%d')
    is_split = BooleanField("Split Expense")
    split_with = IntegerField("Number of People", validators=[NumberRange(min=2)], default=2)
    payments = FieldList(FormField(SplitPaymentForm), min_entries=0)
    submit = SubmitField("Add Expense")

class CreateGroupForm(FlaskForm):
    name = StringField("Group Name", validators=[DataRequired(), Length(min=3, max=100)])
    submit = SubmitField("Create Group")

class JoinGroupForm(FlaskForm):
    invitation_code = StringField("Invitation Code", validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField("Join Group")
