
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_user
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer
from flask_sqlalchemy import SQLAlchemy
from model import  Customer, Purchase, Contactus, Category, Product, Cart
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.orm import declarative_base
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from model import db , app
import random


# Define the signup form
class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

# Define the signup form
class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])

def create_app():# Define the base class for models

    csrf = CSRFProtect(app)
    app.secret_key = 'sttds'  # Add a secret key for flash messages



    # Load and preprocess the data
    df = pd.read_excel(r"./dataset/sttds.xlsx")

    # Prepare the data for product recommendation
    product_features = ['QUANTITY', 'RATINGS', 'PRICE']  # Add relevant features for product recommendation
    product_target = 'PRODUCT_NAME'  # Target variable for product recommendation
    df.columns =['DATE_COL','USER_ID','PRODUCT_ID','PRODUCT_NAME','CATEGORY','QUANTITY' ,'RATINGS','OFFER_ID','PRICE','OFFER_PRICE']
    print(df.columns)
    # Split the data for product recommendation
    product_train_data, product_test_data = train_test_split(df, test_size=0.2, random_state=42)

    # Feature engineering for product recommendation
    product_train_features = product_train_data[product_features]
    product_train_target = product_train_data[product_target]

    # Encode categorical features if necessary
    label_encoder = LabelEncoder()
    for feature in product_features:
        if product_train_features[feature].dtype == 'object':
            product_train_features[feature] = label_encoder.fit_transform(product_train_features[feature])

    product_encoder = LabelEncoder()
    product_encoder.fit(product_train_target)

    # Convert the target variable to a binary matrix using MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    product_train_target_encoded = mlb.fit_transform(product_train_target.apply(lambda x: [x]))
    print(df.columns)
    # Train the Random Forest model for product recommendation
    product_rf_model = RandomForestRegressor()
    product_rf_model.fit(product_train_features, product_train_target_encoded)


    # Prepare the data for offer recommendation
    offer_features = ['QUANTITY', 'RATINGS', 'PRICE']  # Add relevant features for offer recommendation
    offer_target = 'OFFER_ID'  # Target variable for offer recommendation

    # Split the data for offer recommendation
    offer_train_data, offer_test_data = train_test_split(df, test_size=0.2, random_state=42)

    # Encode the 'OFFER ID' column
    label_encoder = LabelEncoder()
    offer_target_encoded = label_encoder.fit_transform(offer_train_data['OFFER_ID'])

    # Create 'OFFER DISCOUNT' column in offer_train_data DataFrame
    offer_train_data['OFFER_DISCOUNT'] = offer_train_data['PRICE'] * (1 - offer_target_encoded)

    # Feature engineering for offer recommendation
    offer_train_features = offer_train_data[offer_features]
    offer_train_target = offer_train_data['OFFER_ID']

    # Encode categorical features if necessary
    for feature in offer_train_features.columns:
        if offer_train_features[feature].dtype == 'object':
            print(feature)
            print(offer_train_features.feature.value_counts())
            offer_train_features[feature] = label_encoder.fit_transform(offer_train_features[feature])

    # Encode target variable
    offer_target_encoded = label_encoder.fit_transform(offer_train_target)

    # Train the Random Forest model for offer recommendation
    offer_rf_model = RandomForestRegressor()
    print(offer_train_features.isna().sum())
    offer_rf_model.fit(offer_train_features, offer_target_encoded)


    def recommend_products_and_offers(user_features):
        # Convert user features to a numpy array
        user_feature = np.array(user_features).reshape(1, -1)

        # Encode categorical features if necessary
        for i, feature_ in enumerate(user_feature[0]):
            if isinstance(feature_, str):
                user_feature[0][i] = label_encoder.transform([feature_])[0]

        # Use the trained models to make predictions
        print()
        product_prediction = product_rf_model.predict(user_feature)
        offer_prediction = offer_rf_model.predict(user_feature)

        # Get the recommended product and offer indices
        product_index = np.argmax(product_prediction)
        print(product_index)
        offer_index = np.argmax(offer_prediction)
        print(offer_index)
        # Get the recommended product and offer names
        product_recommendations = product_encoder.inverse_transform([product_index])[0]
        print(offer_train_data.loc[0,'OFFER_ID'])
        offer_recommendations = offer_train_data.loc[offer_index, 'OFFER_ID']
        # Get the recommended offer discount
        print(offer_train_data.columns)
        print(offer_train_data.loc[offer_train_data['OFFER_ID'] == offer_recommendations, 'OFFER_DISCOUNT'])
        offer_discounts = offer_train_data.loc[offer_train_data['OFFER_ID'] == offer_recommendations, 'OFFER_DISCOUNT'].values[0]
        if offer_discounts < 0.1:
             offer_discounts = np.random.randint(10,40)

        print(product_recommendations, offer_recommendations, offer_discounts)
        return product_recommendations, offer_recommendations, offer_discounts
    with app.app_context():

        db.drop_all() # delete tables if already exists..
        db.create_all() #create all tables
        db.session.add_all([Customer(name="kumar",email='akrajamoni999@gmail.com',password='kumar123'),
                            Customer(name="Dhanush",email='dhanushkunchala98@gmail.com',password='dhanush123'),
                            Customer(name="Vamsi",email='nalamativ@mail.sacredheart.edu',password='admin123'),
                            Customer(name="Adminteam",email='storetodoor2023@outlook.com',password='Store123')
                            ])
        db.session.commit()
        category1 = Category(name='Groceries')
        category2 = Category(name='Clothing')
        category3 = Category(name='Books')
        category4 = Category(name='Electronics')
        category5 = Category(name='Sports & Outdoor')
        category6 = Category(name='Beauty')

        db.session.add_all([category1, category2, category3, category4, category5, category6])
        db.session.commit()

        category_products = {
            'Groceries': [
                {'name': 'Egg Tray', 'description': '30-Cell Egg Crates', 'price': 4.49},
                {'name': 'Bread', 'description': 'Homemade bread', 'price': 1.00},
                {'name': 'Banana', 'description': '1 piece', 'price': 0.50},
                {'name': 'Avocado', 'description': '1 piece', 'price': 0.80},
                {'name': 'Milk', 'description': '1 Gallon', 'price': 4.00},
                {'name': 'Apple', 'description': '1 piece', 'price': 1.99},
            ],
            'Electronics': [
                {'name': 'Speakers', 'description': 'Sony', 'price': 34.99},
                {'name': 'Watches', 'description': 'I Watch Series 8', 'price': 49.99},
                {'name': 'Phones', 'description': 'iPhone 14 128 GB', 'price': 999.99},
                {'name': 'Vacuum', 'description': 'Shark Navigator Lift-Away Deluxe Upright Vacuum NV 360',
                 'price': 189.99},
                {'name': 'Laptops', 'description': '13 inch MacBook Pro - Space Gray', 'price': 1199.99},
                {'name': 'Smart TVs', 'description': 'Sony - 55" Class X75K 4K HDR LED Google TV', 'price': 499.99},
            ],
            'Clothing': [
                {'name': 'Shirt', 'description': 'Mens Stylish O-Neck Henley Shirt', 'price': 9.99},
                {'name': 'Hoodies', 'description': 'Nike Sportswear Club Fleece Zip Hoodie', 'price': 16.99},
                {'name': 'Jackets', 'description': 'Lightweight Water-Resistant Puffer Jacket', 'price': 24.99},
                {'name': 'Trousers', 'description': 'Calvin Klein Mens Modern Fit Dress Pant', 'price': 11.99},
                {'name': 'Dresses', 'description': 'Womens Floral Vintage Dress Elegant Midi Evening Dress',
                 'price': 29.99},
                {'name': 'Tops', 'description': 'Allover Geo Notch Neck Blouse', 'price': 6.99},
            ],
            'Sports & Outdoor': [
                {'name': 'Balls', 'description': 'Adidas FIFA World Cup Qatar 2022 Al Rihla Training Soccer Ball',
                 'price': 12.99},
                {'name': 'Gloves', 'description': 'PEIPU Nitrile Gloves Disposable Gloves (Medium, 100-Count)',
                 'price': 11.99},
                {'name': 'Helmets', 'description': 'Triple Eight Skate-and-Skateboarding-Helmets Sweatsaver Helmet',
                 'price': 44.99},
                {'name': 'Bicycle', 'description': 'Professional Cycle with good seat and gears avaialable', 'price': 20.99},
                {'name': 'Jerseys', 'description': '1 ARGENTINA HOME JERSEY 2022-2023 QATAR 2022 10 MESSI',
                 'price': 11.99},
            ],
            'Books': [
                {'name': 'Pride and Prejudice by Jane Austen', 'description': 'Illustrated by Anna and Elena Balbusso',
                 'price': 13.99},
                {'name': 'Naruto Comic Book', 'description': 'Naruto, Vol. 1: Uzumaki Naruto', 'price': 7.99},
                {'name': 'The Lord of the Rings', 'description': 'by J.R.R. Tolkien', 'price': 17.99},
                {'name': 'The Kite Runner', 'description': 'by Khaled Hosseini', 'price': 13.99},
                {'name': 'Atomic Habits', 'description': 'by James Clear', 'price': 14.99},
                {'name': 'Steve Jobs', 'description': 'by Walter Isaacson', 'price': 11.99},
            ],
            'Beauty': [
                {'name': 'Serums', 'description': '100ml', 'price': 8.99},
                {'name': 'Hair Gel', 'description': '200ml', 'price': 9.99},
                {'name': 'Moisturizers', 'description': '500ml', 'price': 14.99},
                {'name': 'Shampoos', 'description': '200ml', 'price': 6.99},
                {'name': 'Soaps', 'description': '1 piece', 'price': 0.99},
                {'name': 'Body Wash', 'description': '200ml', 'price': 7.99},
            ],
        }

        # Create and associate the categories with their respective products
        for category_name, products in category_products.items():
            category = Category.query.filter_by(name=category_name).first()
            for product_details in products:
                product = Product(
                    name=product_details['name'],
                    description=product_details['description'],
                    price=product_details['price'],
                    category=category
                )
                db.session.add(product)

        #db.create_all()

        db.session.commit()

       

        # Home page - Show categories
        @app.route('/')
        def home():
            categories = Category.query.all()
            return render_template('base.html', categories=categories)

        # Category page - Show products in a category
        @app.route('/category/<int:category_id>')
        def category(category_id):
            print(type(category_id))
            category_ = Category.query.filter_by(id=category_id).first()
            print(category_)
            print(category_.id,category_.name)
            print(Product.query.get(1))
            products = Product.query.filter_by(category_id=category_.id).all()
            print(products)
            template_name = category_.name.lower() + '.html'
            print(template_name)
            return render_template(template_name, category=category_.name, products=products)


        # # Add product to cart
        # @app.route('/add_to_cart', methods=['POST'])
        # def add_to_cart():
        #     print(user.id)
        #     if 'user_id' in session:
        #         customer_id = session['user_id']
        #         product_id = request.form['product_id']
        #         quantity = int(request.form['quantity'])
        
        #         # Check if the product is already in the cart
        #         existing_cart_item = Cart.query.filter_by(customer_id=user_id, product_id=product_id).first()
        #         if existing_cart_item:
        #             existing_cart_item.quantity += quantity
        #         else:
        #             new_cart_item = Cart(customer_id=customer_id, product_id=product_id, quantity=quantity)
        #             db.session.add(new_cart_item)
        
        #         db.session.commit()
        #         return redirect(url_for('cart'))
        #     else:
        #         return redirect(url_for('login'))

        # Cart page - Show cart items
        # @app.route('/cart')
        # def cart():
        #     if 'customer_id' in session:
        #         customer_id = session['customer_id']
        #         cart_items = Cart.query.filter_by(customer_id=customer_id).all()
        #         total_price = sum(item.product.price * item.quantity for item in cart_items)
        #         return render_template('cart.html', cart_items=cart_items, total_price=total_price)
        #     else:
        #         return redirect(url_for('login'))

        # Purchase
        # @app.route('/place_order', methods=['POST'])
        # def place_order():
        #     if 'user_id' in session:
        #         customer_id = session['user_id']
        #         cart_items = session.get('cart', [])

        #         # Process the order and store the cart items in the Purchase model
        #         for item in cart_items:
        #             product_id = item['id']
        #             quantity = item['quantity']

        #             purchase = Purchase(customer_id=customer_id, product_id=product_id, quantity=quantity)
        #             db.session.add(purchase)

        #         db.session.commit()

        #         # Clear the cart after placing the order
        #         session['cart'] = []

        #         return render_template('order_placed.html')
        #     else:
        #         return redirect('/login')


        # About route
        @app.route('/about')
        def about():
            print('Working')
            return render_template('about.html')

        # Contact route
        @app.route('/contact', methods=['GET', 'POST'])
        def contact():
            print('Working')
              # Check if the user is logged in
            if 'user_id' not in session:
                flash('Please login to access your profile.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            user = Customer.query.get(user_id)

          
            if request.method == 'POST':
                message = request.form['message']

                # Create a new contact object
                new_contact = Contactus( message=message)

                # Save the contact object to the database
                db.session.add(new_contact)
                db.session.commit()

                return redirect(url_for('contact_success'))  # Use url_for to get the URL of the contact_success route
            else:
                return render_template('contact.html')

        # Contact success route
        @app.route('/contact-success')
        def contact_success():
            return render_template('contact_success.html')
        
        @app.route('/send_recommendation',methods=['GET','POST'])
        def send_recommendation():
            #Send the recommendation email to the customer
              # # Load the customer data from the database
            customers = Customer.query.all()
            print("customers is ",customers)
            customer_emails = ",".join([customer.email for customer in customers])
            print("Customer emails are :", customer_emails)

          
            send_email(customer_emails, product_recommendation, offer_recommendation, offer_discounts, product_price)
            return render_template('send_recommendation.html')
            

        # Login route
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            print(request.form)
            form = LoginForm(request.form)
            print(request.method,form.validate_on_submit(),form.validate(),form.password.data,form.username.data)
            if request.method == 'POST' and  form.validate():
                email = request.form['username']
                password = request.form['password']

                if email == 'storetodoor2023@outlook.com' and password == 'Store123':
                    session['admin_logged_in'] = True
                    return render_template('send_recommendation.html')

                user = Customer.query.filter_by(email=email).first()
                print(user.id,user.name)


                if not user or not user.check_password(password):
                    flash('Invalid email or password. Please try again.', 'error')
                    return redirect(url_for('login'))


                # Set the user session
                session['user_id'] = user.id
                session['user_name'] = user.name
                print(user.id,user.email,user.password)
                flash('Login successful.', 'success')
                return redirect(url_for('home'))
            else:
                print("Form validation failed")
                return render_template('login.html', form=form)

        # Signup route
        @app.route('/signup', methods=['GET', 'POST'])
        def signup():
            form = SignupForm()
            if request.method == 'POST' and form.validate_on_submit():
                name = form.name.data
                email = form.email.data
                password = form.password.data

                # Check if a user with the same email already exists
                existing_user = Customer.query.filter_by(email=email).first()
                if existing_user:
                    flash('Email already registered', 'error')
                else:
                    # Create a new user
                    new_user = Customer(name=name, email=email, password=password)
                    db.session.add(new_user)
                    db.session.commit()

                    flash('Registration successful', 'success')

                    # Redirect to the login page
                    return redirect(url_for('login'))

            # Render the signup form template
            return render_template('signup.html', form=form)
        # LOGOUT
        @app.route('/logout')
        def logout():
            # Clear the user session
            session.pop('user_id', None)
            flash('Logout successful.', 'success')
            return redirect(url_for('home'))

        # Profile Update
        @app.route('/profile', methods=['GET', 'POST'])
        def profile():
            # Check if the user is logged in
            if 'user_id' not in session:
                flash('Please login to access your profile.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            user = Customer.query.get(user_id)

            if request.method == 'POST':
                name = request.form['name']
                email = request.form['email']

                user.update_profile(name=name, email=email)
                flash('Profile updated successfully.', 'success')
                return redirect(url_for('profile'))
            else:
                return render_template('profile.html', user=user)

        # Order History
        @app.route('/order_history')
        def order_history():
            # Check if the user is logged in
            if 'user_id' in session:
                user_id = session['user_id']
                customer = Customer.query.get(user_id)

                # Get the customer's purchase history
                purchase_history = customer.get_order_history()

                return render_template('order_history.html', purchases=purchase_history)
            else:
                return redirect(url_for('login'))

        # # Step 2: Generate Verification Code
        # def generate_verification_code():
        #     # Generate a random 6-digit verification code
        #     return str(random.randint(100000, 999999))

        # # Step 3: Send Email with Verification Code
        # def send_verification_email(to_email, verification_code):
        #     smtp_server = 'smtp-mail.outlook.com'
        #     smtp_port = 587  # Replace with the appropriate SMTP port
        #     smtp_username = 'storetodoor2023@outlook.com'  # Replace with your SMTP username
        #     smtp_password = 'sttds@123'  # Replace with your SMTP password

        #     # Compose the email message
        #     subject = 'Password Reset Verification Code'
        #     body = f'Your verification code is: {verification_code}'
        #     message = f'Subject: {subject}\n\n{body}'

        #     try:
        #         # Connect to the SMTP server
        #         server = smtplib.SMTP(smtp_server, smtp_port)
        #         server.starttls()
        #         server.login(smtp_username, smtp_password)

        #         # Send the email
        #         server.sendmail(smtp_username, to_email, message)
        #         server.quit()
        #         return True
        #     except Exception as e:
        #         print('Error sending email:', str(e))
        #         return False

        # # Step 1: Forgot Password Request
        # @app.route('/forgot_password', methods=['GET', 'POST'])
        # def forgot_password():
        #     if request.method == 'POST':
        #         email = request.form['email']

        #         # Step 2: Generate Verification Code
        #         verification_code = generate_verification_code()

        #         # Step 3: Send Email with Verification Code
        #         if send_verification_email(email, verification_code):
        #             # Store the verification code in the session
        #             session['verification_code'] = verification_code
        #             session['email'] = email
        #             flash('A verification code has been sent to your email.')
        #             return redirect('/verify_code')
        #         else:
        #             flash('Failed to send the verification code. Please try again.')

        #     return render_template('forgot_password.html')

        # # Step 4: Verification Page
        # @app.route('/verify_code', methods=['GET', 'POST'])
        # def verify_code():
        #     if 'verification_code' not in session or 'email' not in session:
        #         return redirect('/forgot_password')

        #     if request.method == 'POST':
        #         entered_code = request.form['verification_code']
        #         email = session['email']
        #         stored_code = session['verification_code']

        #         # Step 5: Verify Code
        #         if entered_code == stored_code:
        #             # Verification code is valid, proceed to password reset page
        #             return redirect('/reset_password')
        #         else:
        #             flash('Invalid verification code. Please try again.')

        #     return render_template('verify_code.html')

        # # Step 6: Password Reset
        # @app.route('/reset_password', methods=['GET', 'POST'])
        # def reset_password():
        #     if 'verification_code' not in session or 'email' not in session:
        #         return redirect('/forgot_password')

        #     if request.method == 'POST':
        #         new_password = request.form['new_password']
        #         email = session['email']

        #         # Step 7: Update Password
        #         # Update the password for the user associated with the email in the database

        #         flash('Your password has been reset successfully.')
        #         session.pop('verification_code')
        #         session.pop('email')
        #         return redirect('/login')

        #     return render_template('reset_password.html')

        # # # Load the customer data from the database
        customers = Customer.query.all()
        print("customers is ",customers)

        # Convert the customer data into a pandas DataFrame
        customer_data = pd.DataFrame([(customer.name, customer.email) for customer in customers], columns=['Name', 'Email'])
        

        # Add item to cart
        @app.route('/add_to_cart/<int:product_id>', methods=['POST'])
        def add_to_cart(product_id):
            if 'user_id' in session:
                customer_id = session['user_id']
                quantity = int(request.form['quantity'])

                # Check if the item already exists in the cart
                cart_item = Cart.query.filter_by(customer_id=customer_id, product_id=product_id).first()

                if cart_item:
                    # If the item exists, update the quantity
                    cart_item.quantity += quantity
                else:
                    # If the item doesn't exist, create a new cart item
                    cart_item = Cart(customer_id=customer_id, product_id=product_id, quantity=quantity)
                    db.session.add(cart_item)

                db.session.commit()

                # Update the cart icon number in the session
                cart_count = session.get('cart_count', 0)
                session['cart_count'] = cart_count + quantity

                flash('Item added to cart', 'success')
                return redirect(url_for('cart'))
            else:
                return redirect('/login')

        # Function to send email
        def send_email(customer_email, product_recommendations, offer_recommendations, offer_discounts, product_price):
            # Compose the email message
            print("customer mail is", customer_email)
            message = MIMEMultipart()
            message['From'] = 'storetodoor2023@outlook.com'  # Replace with your email address
            
            message['To'] = customer_email
            
            message['Subject'] = 'Product Recommendation and Offer!!!!'

            # Email body
            email_body = f"Dear Customer,\n\nWe recommend the following product:\n\nProduct: {product_recommendations}\n Product price : {product_price}\nOffer: {offer_recommendations}\nDiscount: {offer_discounts}%\n\nThank you for shopping with us!\n\nBest Regards,\nThe Admin Team"

            message.attach(MIMEText(email_body, 'plain'))

            # Connect to the SMTP server and send the email
            smtp_server = 'smtp-mail.outlook.com'
            smtp_port = 587  # Replace with the appropriate SMTP port
            smtp_username = 'storetodoor2023@outlook.com'  # Replace with your SMTP username
            smtp_password = 'sttds@123'  # Replace with your SMTP password

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(message['From'], message['To'], message.as_string())

        print(customers)
        # Iterate over each customer
        for customer in customers:
            print(customer)
            # # Retrieve the customer's purchase history from the database
            print(Purchase.query.all())
            Purchase_ =Purchase.query.filter(Purchase.customer_id==customer.id)
            print(Purchase_)
            #Quantity = Cart.query.filter(Cart.customer_id==customer)
            print(type(Purchase_))
            print(Purchase_)
            # Convert the purchase history into a pandas DataFrame
            purchase_data = pd.DataFrame([(Purchase_.product_name, Purchase_.ratings, Purchase_.price) for purchase in Purchase_], columns=['Product Name', 'Ratings', 'Price'])
            price = np.random.randint(30)
            # # Perform product and offer recommendations based on the purchase history
            user_features = [np.random.randint(5), np.random.randint(100),price]  # Example: Using average ratings and average price
            print(user_features)

            product_recommendation, offer_recommendation, offer_discounts = recommend_products_and_offers(user_features)
            product_price = price *(1- offer_discounts)
            # Send the recommendation email to the customer
           # send_email(customer.email, product_recommendation, offer_recommendation, offer_discounts, product_price)

    return app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

