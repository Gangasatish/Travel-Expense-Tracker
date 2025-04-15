from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from io import BytesIO
import matplotlib.pyplot as plt
from chatbot import chat
from forms import CreateGroupForm, LoginForm, RegistrationForm, ExpenseForm, JoinGroupForm, SplitPaymentForm
from models import Group, ExpenseSplit
from extensions import db, bcrypt, login_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User, Expense
import tempfile
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ExpenseForm()
    if form.validate_on_submit():
        group_id = request.form.get('group_id')
        expense = Expense(
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            user_id=current_user.id,
            group_id=group_id if group_id else None
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get user's groups
    groups = current_user.groups.all()
    
    # Get personal expenses
    personal_expenses = Expense.query.filter_by(user_id=current_user.id, group_id=None).all()
    
    # Get group expenses
    group_expenses = {}
    for group in groups:
        group_expenses[group.id] = Expense.query.filter_by(group_id=group.id).all()
    
    return render_template('dashboard.html', 
                           form=form, 
                           personal_expenses=personal_expenses,
                           groups=groups,
                           group_expenses=group_expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        try:
            expense = Expense(
                amount=form.amount.data,
                category=form.category.data,
                date=form.date.data,
                user_id=current_user.id,
                is_split=form.is_split.data
            )
            db.session.add(expense)
            db.session.flush()

            if form.is_split.data:
                if not form.payments.data:
                    flash('Please add at least one person to split with.', 'danger')
                    return render_template('add_expense.html', form=form)

                total_amount = form.amount.data
                num_people = form.split_with.data
                if num_people < 2:
                    flash('Number of people must be at least 2 for split expenses.', 'danger')
                    return render_template('add_expense.html', form=form)

                amount_per_person = total_amount / num_people
                total_paid = 0

                # Create splits for each person
                for payment_form in form.payments:
                    if not User.query.get(payment_form.user_id.data):
                        flash('One or more selected users do not exist.', 'danger')
                        return render_template('add_expense.html', form=form)

                    split = ExpenseSplit(
                        expense_id=expense.id,
                        user_id=payment_form.user_id.data,
                        amount_owed=amount_per_person,
                        amount_paid=payment_form.amount_paid.data
                    )
                    total_paid += payment_form.amount_paid.data
                    db.session.add(split)

                # Verify total paid amount matches expense amount
                if abs(total_paid - total_amount) > 0.01:  # Using small epsilon for float comparison
                    flash('Total paid amount must equal the expense amount.', 'danger')
                    return render_template('add_expense.html', form=form)

            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the expense. Please try again.', 'danger')
            return render_template('add_expense.html', form=form)

    return render_template('add_expense.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroupForm()
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            creator_id=current_user.id,
            invitation_code=Group.generate_invitation_code()
        )
        db.session.add(group)
        group.members.append(current_user)
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_group.html', form=form)

@app.route('/join_group', methods=['GET', 'POST'])
@login_required
def join_group():
    form = JoinGroupForm()
    if form.validate_on_submit():
        try:
            invitation_code = form.invitation_code.data.strip()
            
            # Basic validation
            if not invitation_code:
                flash('Please enter an invitation code.', 'danger')
                return render_template('join_group.html', form=form)
            
            # Format validation
            if not invitation_code.isdigit():
                flash('Invalid code format. Code must contain only numbers.', 'danger')
                return render_template('join_group.html', form=form)
                
            if len(invitation_code) != 4:
                flash('Invalid code length. Please enter exactly 4 digits.', 'danger')
                return render_template('join_group.html', form=form)

            # Group existence check
            group = Group.query.filter_by(invitation_code=invitation_code).first()
            if not group:
                flash('Group not found. Please verify the invitation code.', 'danger')
                return render_template('join_group.html', form=form)

            # Membership check
            if current_user in group.members:
                flash(f'You are already a member of the group: {group.name}', 'info')
                return redirect(url_for('dashboard'))

            try:
                # Join the group
                group.members.append(current_user)
                db.session.commit()
                flash(f'Successfully joined the group: {group.name}!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash('Failed to join the group. Please try again.', 'danger')
                return render_template('join_group.html', form=form)
            
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template('join_group.html', form=form)
            
    return render_template('join_group.html', form=form)

# Register chatbot route
app.register_blueprint(chat, url_prefix='')

@app.route('/generate_report/<int:group_id>')
@login_required
def generate_report(group_id):
    group = Group.query.get_or_404(group_id)
    if current_user not in group.members:
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('dashboard'))

    # Create a BytesIO buffer for the PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph(f'Expense Report - {group.name}', title_style))
    elements.append(Spacer(1, 12))

    # Prepare expense data
    expenses = Expense.query.filter_by(group_id=group_id).all()
    expense_data = [
        ['Date', 'User', 'Category', 'Amount', 'Split']
    ]
    category_totals = {}
    for expense in expenses:
        split_status = 'Yes' if expense.is_split else 'No'
        expense_data.append([
            expense.date.strftime('%Y-%m-%d'),
            User.query.get(expense.user_id).username,
            expense.category,
            f'${expense.amount:.2f}',
            split_status
        ])
        category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    # Create expense table
    table = Table(expense_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Create pie chart for category distribution
    drawing = Drawing(400, 200)
    pie = Pie()
    pie.x = 75
    pie.y = 0
    pie.width = 250
    pie.height = 200
    pie.data = list(category_totals.values())
    pie.labels = list(category_totals.keys())
    drawing.add(pie)
    elements.append(drawing)

    # Generate balance summary
    elements.append(Spacer(1, 20))
    elements.append(Paragraph('Balance Summary', styles['Heading2']))
    balance_data = [['User', 'Total Paid', 'Total Owed', 'Balance']]
    
    for member in group.members:
        total_paid = sum(split.amount_paid for expense in expenses
                        for split in expense.splits if split.user_id == member.id)
        total_owed = sum(split.amount_owed for expense in expenses
                        for split in expense.splits if split.user_id == member.id)
        balance = total_paid - total_owed
        balance_data.append([
            member.username,
            f'${total_paid:.2f}',
            f'${total_owed:.2f}',
            f'${balance:.2f}'
        ])

    balance_table = Table(balance_data)
    balance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(balance_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'expense_report_{group.name}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
