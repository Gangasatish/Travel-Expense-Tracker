from flask_login import UserMixin
from datetime import datetime
from extensions import db
import random
import string

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invitation_code = db.Column(db.String(4), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    members = db.relationship('User', secondary='user_group', backref=db.backref('groups', lazy='dynamic'))
    expenses = db.relationship('Expense', backref='group', lazy=True)

    @staticmethod
    def generate_invitation_code():
        while True:
            code = ''.join(random.choices(string.digits, k=4))
            if not Group.query.filter_by(invitation_code=code).first():
                return code

user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)
    created_groups = db.relationship('Group', backref='creator', lazy=True, foreign_keys=[Group.creator_id])
    # This relationship is managed by the backref in Group.members
    
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete='SET NULL'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_split = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')
    splits = db.relationship('ExpenseSplit', backref='expense', lazy=True, cascade='all, delete-orphan')
    
    @property
    def payment_status(self):
        if not self.is_split:
            return 'not_split'
        if self.is_settled:
            return 'settled'
        if self.total_paid > 0:
            return 'partially_paid'
        return 'pending'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount <= 0:
            raise ValueError('Expense amount must be positive')
        if not self.category:
            raise ValueError('Category is required')
    
    @property
    def total_paid(self):
        return sum(split.amount_paid for split in self.splits)
    
    @property
    def is_settled(self):
        if not self.is_split:
            return True
        return all(split.amount_paid >= split.amount_owed for split in self.splits)
    
    def get_user_split(self, user_id):
        return next((split for split in self.splits if split.user_id == user_id), None)

class ExpenseSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    amount_owed = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('expense_splits', lazy=True, cascade='all, delete-orphan'))
    
    @property
    def balance(self):
        return self.amount_paid - self.amount_owed
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.amount_owed < 0:
            raise ValueError('Amount owed cannot be negative')
        if self.amount_paid < 0:
            raise ValueError('Amount paid cannot be negative')
