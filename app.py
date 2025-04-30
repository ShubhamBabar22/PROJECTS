# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
# Configure secret key for session management and security
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
# Configure SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'

# Initialize SQLAlchemy for database operations
db = SQLAlchemy(app)
# Initialize LoginManager for user authentication
login_manager = LoginManager()
login_manager.init_app(app)
# Set the login view for redirecting unauthorized users
login_manager.login_view = 'login'

# User model for database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # Relationship with Expense model (one-to-many)
    expenses = db.relationship('Expense', backref='user', lazy=True)

    # Method to set password with hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check password against hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Expense model for database
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign key relationship with User model
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for home page
@app.route('/')
def index():
    # Redirect to dashboard if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        # Check credentials and log in user
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    return render_template('login.html')

# Route for dashboard (requires login)
@app.route('/dashboard')
@login_required
def dashboard():
    # Get all expenses for current user, ordered by date
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('dashboard.html', expenses=expenses)

# Route for adding new expense (requires login)
@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    # Get form data
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    category = request.form.get('category')
    
    # Create new expense
    expense = Expense(amount=amount, description=description, category=category, user_id=current_user.id)
    db.session.add(expense)
    db.session.commit()
    
    flash('Expense added successfully!')
    return redirect(url_for('dashboard'))

# Route for user logout (requires login)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Run the application
if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    # Start Flask development server
    app.run(debug=True) 