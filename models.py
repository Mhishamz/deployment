from app import db



class Customer(db.Model):
    __tablename__ = 'Customers'

    customer_id = db.Column(db.String(20), primary_key=True)
    customer_name = db.Column(db.String(50), nullable=False)
    segment = db.Column(db.String(50))
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Customer {self.customer_name}>'

    def check_password(self, password):
        #return bcrypt.check_password_hash(self.password_hash, password)
        return self.password_hash==password
    def get_id(self):
        return self.customer_id
    

class Product(db.Model):
    __tablename__ = 'Products'

    product_id = db.Column(db.String(20), primary_key=True)
    product_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    sub_category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    size = db.Column(db.Numeric(10, 2), nullable=False)
    ImageData = db.Column(db.LargeBinary, nullable=True)  # Equivalent to VARBINARY(MAX)

    def __repr__(self):
        return f'<Product {self.product_name}>'
    
    def get_price(self):
        return self.price


class CustomerOrder(db.Model):
    __tablename__ = 'Customer_Orders'

    order_id = db.Column(db.String(20), primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('Customers.customer_id'))
    order_date = db.Column(db.DateTime, server_default=db.func.now())
    order_status = db.Column(db.String(25))
    order_priority = db.Column(db.String(25))

    customer = db.relationship('Customer', backref='orders')

    def __repr__(self):
        return f'<Order {self.order_id}>'


class Inventory(db.Model):
    __tablename__ = 'INVENTORY'

    product_id = db.Column(db.String(20), db.ForeignKey('Products.product_id'), primary_key=True, nullable=False)
    statee = db.Column(db.String(75), primary_key=True, nullable=False)
    quantity_in_hand = db.Column(db.Integer, nullable=False)
    country = db.Column(db.String(75), nullable=False)
    city = db.Column(db.String(75), nullable=False)

    product = db.relationship('Product', backref='inventory_items')

    def __repr__(self):
        return f'<Inventory {self.product_id} - {self.statee}>'


class CustomerOrderItem(db.Model):
    __tablename__ = 'Customer_Order_Items'

    order_id = db.Column(db.String(20), db.ForeignKey('Customer_Orders.order_id'), primary_key=True, nullable=False)
    product_id = db.Column(db.String(20), db.ForeignKey('Products.product_id'), primary_key=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Numeric(10, 2), nullable=False)

    customer_order = db.relationship('CustomerOrder', backref='order_items')
    product = db.relationship('Product', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.order_id} - {self.product_id}>'
