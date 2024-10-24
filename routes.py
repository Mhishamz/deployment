from flask import render_template,request,redirect,url_for,session,Response , jsonify,flash
from models import *
import string
import random
from sqlalchemy import func
from datetime import datetime
import pickle
import pandas as pd
import os


def register_routes(app,db):
    
    @app.route('/')
    def index():
        return render_template('login.html')

        
    @app.route('/login',methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Retrieve the form data
            email = request.form['email']
            password = request.form['password']

            customer = Customer.query.filter_by(email=email).first()

            if email=="Admin" and password=='12345':
                session['id']="admin"
                return redirect(url_for('admin'))
            
            if customer and customer.check_password(password):
                session['id']=customer.get_id()
                return redirect(url_for('products'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('login.html', error=error)
    
        else:
            return render_template('login.html')

    def Add_customer(name,segment,email,password_hash):
        # Split the name into parts and get the first letter of each part
        name_parts = name.split()
        id_prefix = ''.join(part[0].upper() for part in name_parts[:2])  # Get first letters of first two names

        # Generate a random 6-digit number
        while True:
            random_number = ''.join(random.choices(string.digits, k=6))
            customer_id = f"{id_prefix}-{random_number}"
            
            # Check if the ID exists in the database
            if not Customer.query.filter_by(customer_id=customer_id).first():
                new_customer = Customer(customer_id=customer_id,customer_name=name,segment=segment,password_hash=password_hash,email=email)
                #db.add(new_customer)
                #db.commit()
                db.session.add(new_customer)
                db.session.commit()
                return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            # Retrieve form data
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            segment = request.form.get('segment')


            if Customer.query.filter_by(email=email).first():
                # If the email already exists, display an error message
                error_message = 'Email already exists. Please choose a different email.'
                return render_template('signup.html', error_message=error_message)
            else:
                # Insert the user data into the database
                Add_customer(name=name,segment=segment,password_hash=password,email=email)


            # Create a session for the user
            #session['email'] = email

            # Redirect to the profile page
            return redirect(url_for('login'))
        else:
            return render_template('signup.html')


    @app.route('/products')
    def products(limit=20):
        random_products = Product.query.order_by(func.newid()).limit(limit).all()
        return render_template('shop.html', products=random_products)


    @app.route('/search')
    def search():
        # Get the search query from the request's query parameters
        query = request.args.get('query', '')
        
        # Query the database for products that match the search query
        random_products = (
            Product.query
            .filter(Product.product_name.ilike(f'%{query}%'))  # Use ilike for case-insensitive search
            .order_by(func.newid())  # Order results randomly
            .limit(20)  # Limit to 20 results
            .all()
        )


        return render_template('search_results.html', products=random_products, query=query)


    @app.route('/image/<product_id>')
    def get_image(product_id):
        product = Product.query.get(product_id)
        if product and product.ImageData:
            return Response(product.ImageData, mimetype='image/jpg')  # Adjust mimetype if needed
        return "Image not found", 404
    


    @app.route('/filter_products')
    def filter_products():
        category = request.args.get('category')
        
        if category == 'all':
            filtered_products = Product.query.order_by(func.newid()).limit(20).all() # Get all products
        else:
            filtered_products = Product.query.filter_by(category=category).order_by(func.newid()).limit(20).all()
        
        # Convert the results to a list of dictionaries for JSON response
        products_list = [
            {
                'product_id': product.product_id,
                'product_name': product.product_name,
                'sub_category': product.sub_category,
                'price': product.price,
                'size': product.size,
                'image_url': url_for('get_image', product_id=product.product_id)  # Use the image route
            }
            for product in filtered_products
        ]
        
        return jsonify(products_list)


    @app.route('/product/<product_id>')
    def product_detail(product_id):
        product = Product.query.filter_by(product_id=product_id).first()
            # Get unique states
        unique_states = db.session.query(Inventory.statee).filter_by(product_id=product_id).distinct().all()
        unique_states = [state[0] for state in unique_states]  # Convert to list

        if product:
            return render_template('Product_details.html', product=product,states=unique_states)
        return "Product not found", 404
    
    @app.route('/confirm_order', methods=['POST'])
    def confirm_order():
        # ################################################## 
        if 'id' not in session:
            return redirect(url_for('login'))
        #####################################################
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        priority = request.form.get('priority')
        state = request.form['state']


            # Check if the product exists in inventory and if there's enough quantity
        #inventory_item = Inventory.query.filter_by(product_id=product_id).first()
        inventory_item = Inventory.query.filter_by(product_id=product_id, statee=state).first()

        if not inventory_item:
            return jsonify({'status': 'error', 'message': 'Product not found in inventory.'}), 404
        
        if inventory_item.quantity_in_hand < quantity:
            return jsonify({'status': 'error', 'message': 'Insufficient quantity in inventory.'}), 400

            # Update inventory quantity
        inventory_item.quantity_in_hand -= quantity
        db.session.commit()


        # Generate order ID
        year = datetime.now().year
        while True:
            random_numbers = ''.join(random.choices(string.digits, k=6))
            order_id = f"{year}-{random_numbers}"
            
            # Check if order_id exists
            if not CustomerOrder.query.filter_by(order_id=order_id).first():
                break

        # Create CustomerOrder object
        new_order = CustomerOrder(
            order_id=order_id,
            customer_id=session['id'],  # Replace with the actual customer ID
            order_status='Pending',  # You can modify this as needed
            order_priority=priority
        )

        db.session.add(new_order)
        db.session.commit()

        # Calculate sales
        product = Product.query.filter_by(product_id=product_id).first()
        if product:
            sales = quantity * product.get_price()  # Assuming price is accessible here

            # Create CustomerOrderItem object
            order_item = CustomerOrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                sales=sales
            )
            
            db.session.add(order_item)
            db.session.commit()

        return redirect(url_for('products'))


    @app.route('/customer_orders')
    def customer_orders():
        ######################################################
        if 'id' not in session:
            return redirect(url_for('login'))
        # Retrieve orders for the given customer ID

        customer_id=session['id']
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).all()
        
        return render_template('customer_order.html', orders=orders)
    

    @app.route('/inventory_quantity', methods=['POST'])
    def get_inventory_quantity():
        product_id = request.form['product_id']
        state = request.form['state']

        # Get the inventory item for the specified product and state
        inventory_item = Inventory.query.filter_by(product_id=product_id, statee=state).first()

        if inventory_item:
            return jsonify({'quantity_in_hand': inventory_item.quantity_in_hand})
        
        return jsonify({'quantity_in_hand': 0})  # Return 0 if not found
    
    @app.route('/logout')
    def logout():
        # Clear the session
        session.clear()  # or session.pop('user_id', None) if you only want to clear a specific key
        
        # Optionally, show a message
        flash('You have been logged out successfully.', 'success')
        
        # Redirect to the login page or homepage
        return redirect(url_for('login'))
    





    # Route to display products
    @app.route('/admin', methods=['GET'])
    def admin():

        search_query = request.args.get('search', '')  # Capture the search query from the request
        if search_query:
            # Filter products based on search query (case-insensitive search)
            filtered_products = Product.query.filter(
                Product.product_name.ilike(f'%{search_query}%') |
                Product.category.ilike(f'%{search_query}%') |
                Product.sub_category.ilike(f'%{search_query}%')
            ).limit(20).all()
        else:
            # Default product list if no search query
            filtered_products = Product.query.order_by(func.newid()).limit(20).all()

        return render_template('index.html', products=filtered_products ,search_query=search_query)

    # Route to add a new product
    @app.route('/add', methods=['GET', 'POST'])
    def add_product():
        if request.method == 'POST':
            product_name = request.form['product_name']
            category = request.form['category']
            sub_category = request.form['sub_category']
            price = request.form['price']
            size = request.form['size']
            image = request.files['image'].read() if 'image' in request.files else None
            

                    # Split the name into parts and get the first letter of each part
            initials = ''.join([part[0].upper() for part in product_name.split()])

            # Generate a random 6-digit number and concatenate with initials
            while True:
                random_number = random.randint(100000, 999999)
                product_id = f"{initials}{random_number}"

                # Check if the ID already exists in the database
                if not Product.query.filter_by(product_id=product_id).first():
                    break  # If it doesn't exist, break the loop

            new_product = Product(
                product_id=product_id,
                product_name=product_name,
                category=category,
                sub_category=sub_category,
                price=price,
                size=size,
                ImageData=image
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin'))
        
        return render_template('add_product.html')

    # Route to edit a product
    @app.route('/edit/<string:product_id>', methods=['GET', 'POST'])
    def edit_product(product_id):
        product = Product.query.get_or_404(product_id)

        if request.method == 'POST':
            product.product_name = request.form['product_name']
            product.category = request.form['category']
            product.sub_category = request.form['sub_category']
            product.price = request.form['price']
            product.size = request.form['size']
            if 'image' in request.files and request.files['image'].read():
                product.ImageData = request.files['image'].read()

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin'))
        
        return render_template('edit_product.html', product=product)

    # Route to delete a product
    @app.route('/delete/<string:product_id>', methods=['POST'])
    def delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
        return redirect(url_for('admin'))
    

    

    # Get the absolute path to the 'machine' folder
    base_path = os.path.abspath(os.path.dirname(__file__))
    machine_folder = os.path.join(base_path, 'machine')

    # Load the model and encoders
    with open(os.path.join(machine_folder, 'Sales_model.pkl'), 'rb') as model_file:
        model_best = pickle.load(model_file)

    with open(os.path.join(machine_folder, 'encoder_Sales1.pkl'), 'rb') as encoder_file1:
        encoder = pickle.load(encoder_file1)

    with open(os.path.join(machine_folder, 'encoder_Sales2.pkl'), 'rb') as encoder_file2:
        encoder2 = pickle.load(encoder_file2)

    with open(os.path.join(machine_folder, 'encoder_Sales3.pkl'), 'rb') as encoder_file3:
        encoder3 = pickle.load(encoder_file3)

    sub_categories = encoder.categories_[0]
    countries = encoder2.categories_[0]
    quartiles = encoder3.categories_[0]


    @app.route('/predict', methods=['GET', 'POST'])
    def predict():
        if request.method == 'POST':
            sub_category = request.form['sub_category']
            country = request.form['country']
            quartile = request.form['quartile']

            # Perform prediction using the selected values
            prediction = Test(sub_category, country, quartile)
            return render_template('predict.html', sub_categories=sub_categories, countries=countries, quartiles=quartiles, prediction=prediction)
        
        return render_template('predict.html', sub_categories=sub_categories, countries=countries, quartiles=quartiles, prediction=None)

    def Test(Sub_Category, Country, Quartile):
        row = pd.DataFrame({'Sub.Category': [Sub_Category], 'Country': [Country], 'Quarter_Only': [Quartile]})
        
        encoded_array = encoder.transform(row[['Sub.Category']])
        encoded_df = pd.DataFrame(encoded_array, columns=encoder.get_feature_names_out(['Sub.Category']))
        
        encoded_array2 = encoder2.transform(row[['Country']])
        encoded_df2 = pd.DataFrame(encoded_array2, columns=encoder2.get_feature_names_out(['Country']))
        
        encoded_array3 = encoder3.transform(row[['Quarter_Only']])
        encoded_df3 = pd.DataFrame(encoded_array3, columns=encoder3.get_feature_names_out(['Quarter_Only']))
        
        df_result = pd.concat([encoded_df, encoded_df2, encoded_df3], axis=1)
        res = model_best.predict(df_result)
        final = (res * 40547.745684) + 46481.268382
        
        return final[0]   