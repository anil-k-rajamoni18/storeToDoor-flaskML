from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash
from dataclasses import dataclass


db = SQLAlchemy()


@dataclass
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(128))

    purchases = db.relationship('Purchase', backref='customer', lazy=True)
    contactus = db.relationship('Contactus', backref='customer', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return self.password.strip() == password.strip()
        # return check_password_hash(self.password, password)

    def update_profile(self, name, email):
        self.name = name
        self.email = email
        db.session.commit()

    def change_password(self, new_password):
        self.set_password(new_password)
        db.session.commit()

    def get_order_history(self):
        return Purchase.query.filter_by(customer_id=self.id).all()
@dataclass
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_name = db.Column(db.String(100))
    ratings = db.Column(db.Float)
@dataclass
class Contactus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    message = db.Column(db.Text)
@dataclass
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    products = db.relationship('Product', backref='category')
@dataclass
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
@dataclass
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer)
