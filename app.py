from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'jai_bhole_supermarket_secret_key' # Change this for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(50), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    items = db.Column(db.Text, nullable=False) # Storing items as JSON string

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    all_products = Product.query.all()
    products_by_category = {}
    for product in all_products:
        products_by_category.setdefault(product.category, []).append(product)
    
    store_images = [
        url_for('static', filename='img/interior1.webp'),
        url_for('static', filename='img/interior2.webp'),
        url_for('static', filename='img/interior3.webp'),
        url_for('static', filename='img/interior4.webp'),
        url_for('static', filename='img/interior5.webp'),
        url_for('static', filename='img/interior6.webp'),
        url_for('static', filename='img/interior7.webp'),
    ]
    
    return render_template('index.html', products_by_category=products_by_category, store_images=store_images)

@app.route('/about')
def about():
    return render_template('about.html', about_image=url_for('static', filename='img/exterior1.jpg'))

@app.route('/contact')
def contact():
    return render_template('contact.html', contact_image=url_for('static', filename='img/interior2.webp'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists', 'danger')
        else:
            hashed_password = generate_password_hash(password, method='scrypt')
            new_user = User(name=name, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    data = request.get_json()
    items = data.get('items')
    total_price = data.get('total')
    
    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'})
    
    order = Order(
        user_id=session['user_id'],
        total_price=total_price,
        items=json.dumps(items),
        status='Pending'
    )
    db.session.add(order)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order placed successfully!'})

@app.route('/admin')
@admin_required
def admin():
    # Stats
    orders = Order.query.order_by(Order.id.desc()).all()
    products = Product.query.all()
    total_revenue = sum(order.total_price for order in orders)
    total_orders = len(orders)
    total_products = len(products)
    
    # Parse items for orders
    formatted_orders = []
    for order in orders:
        formatted_orders.append({
            'id': order.id,
            'user': order.user.name,
            'total': order.total_price,
            'status': order.status,
            'order_items': json.loads(order.items)
        })
        
    return render_template('admin.html', 
                         orders=formatted_orders, 
                         products=products,
                         stats={
                             'revenue': total_revenue,
                             'orders': total_orders,
                             'products': total_products
                         })

@app.route('/admin/order/<int:order_id>/update', methods=['POST'])
@admin_required
def update_order_status(order_id):
    status = request.form.get('status')
    order = Order.query.get_or_404(order_id)
    order.status = status
    db.session.commit()
    flash(f'Order #{order_id} status updated to {status}', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/product/add', methods=['POST'])
@admin_required
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    category = request.form.get('category')
    image_url = request.form.get('image_url')
    
    new_product = Product(name=name, price=float(price), category=category, image_url=image_url)
    db.session.add(new_product)
    db.session.commit()
    flash('Product added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/product/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/init_db')
def init_db():
    db.create_all()
    # Seed Data
    if not User.query.filter_by(email='admin@jaibhole.com').first():
        admin = User(
            name='Admin',
            email='admin@jaibhole.com',
            password=generate_password_hash('admin123', method='scrypt'),
            is_admin=True
        )
        db.session.add(admin)
        
    # Seed Products
    if Product.query.count() == 0:
        products = [
            Product(name='Fresh Apples', price=120, category='Fruits', image_url='https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
            Product(name='Organic Bananas', price=40, category='Fruits', image_url='https://images.unsplash.com/photo-1571771896612-618da8fd8b00?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
            Product(name='Whole Wheat Bread', price=35, category='Bakery', image_url='https://images.unsplash.com/photo-1509440159596-0249088772ff?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
            Product(name='Farm Fresh Milk', price=55, category='Dairy', image_url='https://images.unsplash.com/photo-1563636619-e9143da7973b?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
            Product(name='Basmati Rice (1kg)', price=180, category='Grains', image_url='https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
            Product(name='Premium Chocolate', price=250, category='Snacks', image_url='https://images.unsplash.com/photo-1542843137-8791a69ea4d4?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&q=60'),
        ]
        db.session.add_all(products)
        
    db.session.commit()
    return 'Database initialized and seeded!'

if __name__ == '__main__':
    app.run(debug=True)
