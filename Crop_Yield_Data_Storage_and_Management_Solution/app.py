"""
Crop Yield Data Storage and Management Solution
A cloud-ready Flask application for agricultural data management
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# =============================================================================
# DUMMY DATA STORAGE (Replace with DynamoDB integration later)
# =============================================================================

# In-memory user storage (TODO: Replace with DynamoDB)
users_db = {
    'farmers': {},
    'admins': {}
}

# In-memory yield records storage (TODO: Replace with DynamoDB)
yield_records_db = []

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth_admin'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_yields(email):
    """Get yield records for a specific user"""
    return [r for r in yield_records_db if r['user_email'] == email]

def get_all_users():
    """Get all registered users"""
    all_users = []
    for email, data in users_db['farmers'].items():
        all_users.append({
            'email': email,
            'name': data['name'],
            'role': 'Farmer'
        })
    for email, data in users_db['admins'].items():
        all_users.append({
            'email': email,
            'name': data['name'],
            'role': 'Admin'
        })
    return all_users

# =============================================================================
# PUBLIC ROUTES
# =============================================================================

@app.route('/')
def index():
    """Landing page - public access"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page - public access"""
    return render_template('about.html')

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/auth')
def auth():
    """Farmer authentication page"""
    if 'user' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('auth.html')

@app.route('/auth/admin')
def auth_admin():
    """Admin authentication page"""
    if 'user' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('auth_admin.html')

@app.route('/signup/farmer', methods=['POST'])
def signup_farmer():
    """Handle farmer registration"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    # Validation
    if not all([name, email, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('auth'))
    
    if email in users_db['farmers'] or email in users_db['admins']:
        flash('Email already registered.', 'error')
        return redirect(url_for('auth'))
    
    # TODO: Hash password and store in DynamoDB
    users_db['farmers'][email] = {
        'name': name,
        'password': password,  # TODO: Use proper hashing (bcrypt)
        'created_at': datetime.now().isoformat()
    }
    
    # TODO: Send SNS notification for new registration
    
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('auth'))

@app.route('/signup/admin', methods=['POST'])
def signup_admin():
    """Handle admin registration"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    # Validation
    if not all([name, email, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth_admin'))
    
    if len(password) < 8:
        flash('Admin password must be at least 8 characters.', 'error')
        return redirect(url_for('auth_admin'))
    
    if email in users_db['farmers'] or email in users_db['admins']:
        flash('Email already registered.', 'error')
        return redirect(url_for('auth_admin'))
    
    # TODO: Hash password and store in DynamoDB
    users_db['admins'][email] = {
        'name': name,
        'password': password,  # TODO: Use proper hashing (bcrypt)
        'created_at': datetime.now().isoformat()
    }
    
    flash('Admin registration successful! Please log in.', 'success')
    return redirect(url_for('auth_admin'))

@app.route('/login/farmer', methods=['POST'])
def login_farmer():
    """Handle farmer login"""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not all([email, password]):
        flash('Please enter email and password.', 'error')
        return redirect(url_for('auth'))
    
    # TODO: Verify against DynamoDB with hashed password
    user = users_db['farmers'].get(email)
    
    if user and user['password'] == password:
        session['user'] = email
        session['name'] = user['name']
        session['role'] = 'farmer'
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('dashboard'))
    
    flash('Invalid email or password.', 'error')
    return redirect(url_for('auth'))

@app.route('/login/admin', methods=['POST'])
def login_admin():
    """Handle admin login"""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not all([email, password]):
        flash('Please enter email and password.', 'error')
        return redirect(url_for('auth_admin'))
    
    # TODO: Verify against DynamoDB with hashed password
    user = users_db['admins'].get(email)
    
    if user and user['password'] == password:
        session['user'] = email
        session['name'] = user['name']
        session['role'] = 'admin'
        flash(f'Welcome back, Administrator {user["name"]}!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    flash('Invalid admin credentials.', 'error')
    return redirect(url_for('auth_admin'))

@app.route('/logout')
def logout():
    """Handle user logout"""
    name = session.get('name', 'User')
    session.clear()
    flash(f'Goodbye, {name}! You have been logged out.', 'info')
    return redirect(url_for('index'))

# =============================================================================
# FARMER DASHBOARD ROUTES
# =============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Farmer dashboard - view yield records"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    user_email = session.get('user')
    yields = get_user_yields(user_email)
    
    # Calculate statistics
    total_yields = len(yields)
    total_area = sum(float(y['area']) for y in yields) if yields else 0
    total_production = sum(float(y['yield_amount']) for y in yields) if yields else 0
    
    stats = {
        'total_records': total_yields,
        'total_area': round(total_area, 2),
        'total_production': round(total_production, 2),
        'avg_yield': round(total_production / total_area, 2) if total_area > 0 else 0
    }
    
    return render_template('dashboard.html', yields=yields, stats=stats)

@app.route('/add_yield', methods=['GET', 'POST'])
@login_required
def add_yield():
    """Add new yield record"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        crop_name = request.form.get('crop_name', '').strip()
        season = request.form.get('season', '').strip()
        yield_amount = request.form.get('yield_amount', '')
        area = request.form.get('area', '')
        
        # Validation
        if not all([crop_name, season, yield_amount, area]):
            flash('All fields are required.', 'error')
            return redirect(url_for('add_yield'))
        
        try:
            yield_amount = float(yield_amount)
            area = float(area)
            if yield_amount <= 0 or area <= 0:
                raise ValueError("Values must be positive")
        except ValueError:
            flash('Yield amount and area must be positive numbers.', 'error')
            return redirect(url_for('add_yield'))
        
        # TODO: Store in DynamoDB
        record = {
            'id': len(yield_records_db) + 1,
            'user_email': session.get('user'),
            'user_name': session.get('name'),
            'crop_name': crop_name,
            'season': season,
            'yield_amount': yield_amount,
            'area': area,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        yield_records_db.append(record)
        
        # TODO: Send SNS notification for new yield record
        
        flash('Yield record added successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_yield.html')

# =============================================================================
# ADMIN DASHBOARD ROUTES
# =============================================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard - view all users and records"""
    users = get_all_users()
    yields = yield_records_db
    
    # Calculate admin statistics
    stats = {
        'total_users': len(users),
        'total_farmers': len(users_db['farmers']),
        'total_admins': len(users_db['admins']),
        'total_records': len(yields),
        'total_production': round(sum(float(y['yield_amount']) for y in yields), 2) if yields else 0
    }
    
    return render_template('admin_dashboard.html', users=users, yields=yields, stats=stats)

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    flash('Page not found.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

# =============================================================================
# CONTEXT PROCESSORS
# =============================================================================

@app.context_processor
def inject_now():
    """Inject current datetime into all templates"""
    return {'now': datetime.now()}

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Development server configuration
    # TODO: Use Gunicorn/uWSGI for production on EC2
    app.run(debug=True, host='0.0.0.0', port=5000)
