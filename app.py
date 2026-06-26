from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import csv
from sqlalchemy import func, extract

app = Flask(__name__)
app.config['SECRET_KEY'] = 'coffee-factory-secret-key-2024'
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'coffee-factory-secret-key-2024'

# Database - PostgreSQL on Vercel, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///coffee_factory.db')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ==================== DATABASE MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    membership_number = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    deliveries = db.relationship('Delivery', backref='farmer', lazy=True, foreign_keys='Delivery.farmer_id')
    payments = db.relationship('Payment', backref='farmer', lazy=True, foreign_keys='Payment.farmer_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_delivered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    quality_grade = db.Column(db.String(10), nullable=False)
    collection_center = db.Column(db.String(100), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorder = db.relationship('User', foreign_keys=[recorded_by])

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_earned = db.Column(db.Float, nullable=False)
    deductions = db.Column(db.Float, default=0.0)
    net_payment = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id])

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    creator = db.relationship('User', foreign_keys=[created_by])

class PriceConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quality_grade = db.Column(db.String(10), nullable=False, unique=True)
    price_per_unit = db.Column(db.Float, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== AUTH SETUP ====================
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

    return jsonify([{
        'id': f.id,
        'name': f.full_name,
        'membership': f.membership_number,
        'phone': f.phone or 'N/A'
    } for f in farmers])
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/api/all-farmers')
def api_all_farmers():
    farmers = User.query.filter_by(role='farmer', is_active=True).all()
    return jsonify([{
        'id': f.id,
        'name': f.full_name,
        'membership': f.membership_number,
        'phone': f.phone or 'N/A'
    } for f in farmers])
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        membership_number = request.form.get('membership_number')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, full_name=full_name, phone=phone,
                   membership_number=membership_number, role='farmer')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        username = request.form.get('username')
        membership_number = request.form.get('membership_number')
        user = User.query.filter_by(username=username, membership_number=membership_number).first()
        if user:
            temp_password = 'KCFMS' + str(datetime.now().timestamp())[-6:]
            user.set_password(temp_password)
            db.session.commit()
            flash(f'Password reset! Your temporary password is: {temp_password}', 'success')
            return redirect(url_for('login'))
        flash('Invalid username or membership number.', 'danger')
    return render_template('reset_password.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('modern_change_password.html')

@app.route('/analytics')
@login_required
@role_required(['staff', 'admin'])
def analytics():
    total_farmers = User.query.filter_by(role='farmer').count()
    active_farmers = User.query.filter_by(role='farmer', is_active=True).count()
    total_deliveries = Delivery.query.count()
    total_revenue = db.session.query(func.sum(Payment.amount_earned)).scalar() or 0
    
    quality_data = [Delivery.query.filter_by(quality_grade=g).count() for g in ['Premium', 'A', 'B', 'C']]
    
    months, monthly_data = [], []
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30*i)
        months.append(date.strftime('%b'))
        monthly_data.append(float(db.session.query(func.sum(Delivery.quantity)).filter(
            extract('month', Delivery.date_delivered) == date.month,
            extract('year', Delivery.date_delivered) == date.year).scalar() or 0))
    
    top = db.session.query(User.full_name, func.sum(Delivery.quantity)).join(
        Delivery, Delivery.farmer_id == User.id).filter(User.role == 'farmer').group_by(
        User.id).order_by(func.sum(Delivery.quantity).desc()).limit(10).all()
    
    paid = db.session.query(func.sum(Payment.net_payment)).filter(Payment.status == 'paid').scalar() or 0
    pending = db.session.query(func.sum(Payment.net_payment)).filter(Payment.status == 'pending').scalar() or 0
    
    return render_template('analytics.html', total_farmers=total_farmers, active_farmers=active_farmers,
                         total_deliveries=total_deliveries, total_revenue=total_revenue,
                         quality_data=quality_data, months=months, monthly_data=monthly_data,
                         top_farmers_names=[t[0] for t in top], top_farmers_values=[float(t[1]) for t in top],
                         paid_amount=float(paid), pending_amount=float(pending))
@app.route('/api/offline-sync', methods=['POST'])
def offline_sync():
    """Sync offline deliveries to the server"""
    try:
        data = request.get_json()
        
        # Create delivery record
        delivery = Delivery(
            farmer_id=1,  # Default - staff should select correct farmer
            quantity=float(data.get('quantity', 0)),
            unit='kg',
            quality_grade=data.get('quality', 'B'),
            collection_center=data.get('center', 'Unknown'),
            recorded_by=2,  # Staff ID
            date_delivered=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            notes=f"Offline sync - Farmer: {data.get('farmerName')} (#{data.get('memberNumber')})"
        )
        db.session.add(delivery)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Delivery synced!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
@app.route('/offline')
def offline_recorder():
    return render_template('offline_delivery.html')
# ==================== DASHBOARD ROUTES ====================
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'farmer':
        return redirect(url_for('farmer_dashboard'))
    elif current_user.role == 'staff':
        return redirect(url_for('staff_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

@app.route('/farmer/dashboard')
@login_required
@role_required(['farmer'])
def farmer_dashboard():
    today = datetime.now().date()
    total_deliveries = db.session.query(func.sum(Delivery.quantity)).filter(
        Delivery.farmer_id == current_user.id).scalar() or 0
    total_earned = db.session.query(func.sum(Payment.net_payment)).filter(
        Payment.farmer_id == current_user.id, Payment.status == 'paid').scalar() or 0
    outstanding = db.session.query(func.sum(Payment.net_payment)).filter(
        Payment.farmer_id == current_user.id, Payment.status == 'pending').scalar() or 0
    recent_deliveries = Delivery.query.filter_by(farmer_id=current_user.id).order_by(
        Delivery.date_delivered.desc()).limit(5).all()
    announcements = Announcement.query.filter_by(is_active=True).order_by(
        Announcement.created_at.desc()).limit(3).all()
    quality_data = {}
    for grade in ['Premium', 'A', 'B', 'C']:
        quality_data[grade] = Delivery.query.filter_by(farmer_id=current_user.id, quality_grade=grade).count()
    monthly_data = []
    months_labels = []
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30*i)
        months_labels.append(date.strftime('%b'))
        month_total = db.session.query(func.sum(Delivery.quantity)).filter(
            Delivery.farmer_id == current_user.id,
            extract('month', Delivery.date_delivered) == date.month,
            extract('year', Delivery.date_delivered) == date.year).scalar() or 0
        monthly_data.append(float(month_total))
    return render_template('modern_dashboard_live.html', current_user=current_user,
                         total_deliveries=total_deliveries, total_earned=total_earned,
                         outstanding=outstanding, recent_deliveries=recent_deliveries,
                         announcements=announcements, quality_data=quality_data,
                         monthly_data=monthly_data, months_labels=months_labels)

@app.route('/farmer/deliveries')
@login_required
@role_required(['farmer'])
def farmer_deliveries():
    deliveries = Delivery.query.filter_by(farmer_id=current_user.id).order_by(
        Delivery.date_delivered.desc()).all()
    total_deliveries = db.session.query(func.sum(Delivery.quantity)).filter(
        Delivery.farmer_id == current_user.id).scalar() or 0
    monthly_total = db.session.query(func.sum(Delivery.quantity)).filter(
        Delivery.farmer_id == current_user.id,
        extract('month', Delivery.date_delivered) == datetime.now().month).scalar() or 0
    return render_template('modern_deliveries.html', deliveries=deliveries,
                         total_deliveries=total_deliveries, monthly_total=monthly_total)

@app.route('/farmer/payments')
@login_required
@role_required(['farmer'])
def farmer_payments():
    payments = Payment.query.filter_by(farmer_id=current_user.id).order_by(
        Payment.payment_date.desc()).all()
    total_earned = sum(p.amount_earned for p in payments)
    total_paid = sum(p.net_payment for p in payments if p.status == 'paid')
    outstanding = sum(p.net_payment for p in payments if p.status == 'pending')
    return render_template('modern_payments.html', payments=payments,
                         total_earned=total_earned, total_paid=total_paid,
                         outstanding=outstanding)

@app.route('/farmer/profile')
@login_required
@role_required(['farmer'])
def farmer_profile():
    return render_template('modern_profile.html')

@app.route('/farmer/notifications')
@login_required
@role_required(['farmer'])
def farmer_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).all()
    return render_template('modern_notifications.html', notifications=notifs)

@app.route('/farmer/statement/download')
@login_required
@role_required(['farmer'])
def download_statement():
    format_type = request.args.get('format', 'pdf')
    if format_type == 'pdf':
        return generate_pdf_statement(current_user.id)
    else:
        return generate_excel_statement(current_user.id)
@app.route('/farmer/deliveries/download')
@login_required
@role_required(['farmer'])
def download_deliveries_pdf():
    from reportlab.pdfgen import canvas
    
    farmer = current_user
    deliveries = Delivery.query.filter_by(farmer_id=farmer.id).order_by(
        Delivery.date_delivered.desc()).all()
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Watermark
    c.saveState()
    c.setFont("Helvetica-Bold", 80)
    c.setFillColorRGB(0.78, 0.66, 0.43, alpha=0.06)
    c.translate(width/2 - 200, height/2)
    c.rotate(45)
    c.drawString(-100, 0, "KARUHIU UTHERI")
    c.drawString(-50, -100, "COFFEE CO-OP")
    c.restoreState()
    
    # Header
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.setLineWidth(3)
    c.line(0, height - 120, width, height - 120)
    
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.circle(70, height - 60, 40, fill=True, stroke=False)
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(47, height - 72, "KU")
    
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(150, height - 55, "KARUHIU UTHERI")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.drawString(150, height - 75, "DIGITAL FARMERS COOPERATIVE SOCIETY")
    
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 40, height - 50, "DELIVERY REPORT")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, height - 65, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Farmer info
    y_start = height - 150
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.roundRect(40, y_start - 60, width - 80, 55, 10, fill=True, stroke=True)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, y_start - 25, f"Farmer: {farmer.full_name}")
    c.drawString(60, y_start - 42, f"Member No: {farmer.membership_number}")
    c.drawString(350, y_start - 25, f"Total Deliveries: {len(deliveries)}")
    
    # Table
    y_pos = y_start - 90
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.rect(40, y_pos - 25, width - 80, 25, fill=True, stroke=False)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(1, 1, 1)
    for header, x in [('Date', 50), ('Quantity', 180), ('Grade', 280), ('Center', 360), ('Receipt', 520)]:
        c.drawString(x, y_pos - 18, header)
    
    y_pos -= 40
    c.setFont("Helvetica", 8)
    total_kg = 0
    
    for i, d in enumerate(deliveries):
        if y_pos < 120:
            c.showPage()
            y_pos = height - 50
        if i % 2 == 0:
            c.setFillColorRGB(0.97, 0.97, 0.97)
            c.rect(40, y_pos - 15, width - 80, 18, fill=True, stroke=False)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(50, y_pos - 10, d.date_delivered.strftime('%d/%m/%Y'))
        c.drawString(180, y_pos - 10, f"{d.quantity:.1f} {d.unit}")
        c.drawString(280, y_pos - 10, f"Grade {d.quality_grade}")
        c.drawString(360, y_pos - 10, d.collection_center[:25])
        c.drawString(520, y_pos - 10, f"RCT-{d.id:06d}")
        total_kg += d.quantity
        y_pos -= 18
    
    # Total
    y_pos -= 15
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.setLineWidth(2)
    c.line(40, y_pos, width - 40, y_pos)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(50, y_pos - 15, f"TOTAL: {total_kg:.1f} kg")
    
    # Footer
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.rect(0, 0, width, 50, fill=True, stroke=False)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.drawString(40, 30, "Official document from Karuhiu Utheri Digital Farmers Cooperative Society.")
    c.drawString(40, 18, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}")
    
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                    download_name=f'Karuhiu_Utheri_Deliveries_{farmer.full_name}_{datetime.now().strftime("%Y%m%d")}.pdf')

# ==================== STAFF ROUTES ====================
@app.route('/staff/dashboard')
@login_required
@role_required(['staff'])
def staff_dashboard():
    return redirect(url_for('record_delivery'))

@app.route('/staff/record-delivery', methods=['GET', 'POST'])
@login_required
@role_required(['staff', 'admin'])
def record_delivery():
    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        quality_grade = request.form.get('quality_grade')
        collection_center = request.form.get('collection_center')
        delivery = Delivery(farmer_id=farmer_id, quantity=float(quantity), unit=unit,
                          quality_grade=quality_grade, collection_center=collection_center,
                          recorded_by=current_user.id, date_delivered=datetime.now())
        db.session.add(delivery)
        price_config = PriceConfig.query.filter_by(quality_grade=quality_grade).first()
        if price_config:
            amount = float(quantity) * price_config.price_per_unit
            payment = Payment(farmer_id=farmer_id, amount_earned=amount, deductions=0,
                            net_payment=amount, payment_date=datetime.now(), status='pending')
            db.session.add(payment)
            notification = Notification(user_id=farmer_id, title="New Delivery Recorded",
                content=f"Your delivery of {quantity} {unit} Grade {quality_grade} coffee recorded at {collection_center}.",
                type="delivery")
            db.session.add(notification)
        db.session.commit()
        flash('Delivery recorded successfully!', 'success')
        return redirect(url_for('record_delivery'))
    
    # GET request - show the form
    return render_template('staff_delivery.html')
@app.route('/staff/search-farmer')
@login_required
@role_required(['staff', 'admin'])
def search_farmer():
    query = request.args.get('query', '')
    farmers = User.query.filter(User.role == 'farmer',
        (User.full_name.contains(query) | User.membership_number.contains(query) |
         User.phone.contains(query))).all()
    return jsonify([{'id': f.id, 'name': f.full_name, 'membership': f.membership_number,
                    'phone': f.phone} for f in farmers])

# ==================== ADMIN ROUTES ====================
@app.route('/admin')
@login_required
@role_required(['admin'])
def admin_dashboard():
    total_farmers = User.query.filter_by(role='farmer').count()
    active_farmers = User.query.filter_by(role='farmer', is_active=True).count()
    total_deliveries = Delivery.query.count()
    total_payments = db.session.query(func.sum(Payment.net_payment)).scalar() or 0
    farmers = User.query.filter_by(role='farmer').all()
    return render_template('admin_dashboard.html', total_farmers=total_farmers,
                         active_farmers=active_farmers, total_deliveries=total_deliveries,
                         total_payments=total_payments, farmers=farmers)

@app.route('/admin/add-farmer', methods=['POST'])
@login_required
@role_required(['admin'])
def add_farmer():
    user = User(username=request.form.get('username'), full_name=request.form.get('full_name'),
               phone=request.form.get('phone'), membership_number=request.form.get('membership_number'),
               role='farmer')
    user.set_password(request.form.get('password'))
    db.session.add(user)
    db.session.commit()
    flash('Farmer added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-farmer/<int:farmer_id>')
@login_required
@role_required(['admin'])
def toggle_farmer(farmer_id):
    farmer = User.query.get_or_404(farmer_id)
    farmer.is_active = not farmer.is_active
    db.session.commit()
    flash(f'Farmer account {"activated" if farmer.is_active else "suspended"}!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-prices', methods=['POST'])
@login_required
@role_required(['admin'])
def update_prices():
    for grade in ['Premium', 'A', 'B', 'C']:
        price = request.form.get(f'price_{grade}')
        if price:
            config = PriceConfig.query.filter_by(quality_grade=grade).first()
            if config:
                config.price_per_unit = float(price)
            else:
                db.session.add(PriceConfig(quality_grade=grade, price_per_unit=float(price)))
    db.session.commit()
    flash('Prices updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/announcements', methods=['POST'])
@login_required
@role_required(['admin'])
def create_announcement():
    announcement = Announcement(title=request.form.get('title'), content=request.form.get('content'),
                               created_by=current_user.id)
    db.session.add(announcement)
    db.session.commit()
    flash('Announcement created!', 'success')
    return redirect(url_for('admin_dashboard'))
# ==================== REPORTS ====================
@app.route('/reports')
@login_required
@role_required(['staff', 'admin'])
def reports():
    total_farmers = User.query.filter_by(role='farmer').count()
    total_deliveries = Delivery.query.count()
    total_revenue = db.session.query(func.sum(Payment.amount_earned)).scalar() or 0
    
    quality_data = []
    for grade in ['Premium', 'A', 'B', 'C']:
        quality_data.append(Delivery.query.filter_by(quality_grade=grade).count())
    
    monthly_data = []
    months = []
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30*i)
        months.append(date.strftime('%b'))
        total = db.session.query(func.sum(Delivery.quantity)).filter(
            extract('month', Delivery.date_delivered) == date.month,
            extract('year', Delivery.date_delivered) == date.year).scalar() or 0
        monthly_data.append(float(total))
    
    return render_template('reports.html', total_farmers=total_farmers,
                         total_deliveries=total_deliveries, total_revenue=total_revenue,
                         quality_data=quality_data, months=months, monthly_data=monthly_data)

@app.route('/api/report-pdf')
@login_required
@role_required(['staff', 'admin'])
def report_pdf():
    from reportlab.pdfgen import canvas
    
    report_type = request.args.get('type', 'farmer_produce')
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Watermark
    c.saveState()
    c.setFont("Helvetica-Bold", 80)
    c.setFillColorRGB(0.78, 0.66, 0.43, alpha=0.06)
    c.translate(width/2-200, height/2)
    c.rotate(45)
    c.drawString(-100, 0, "KARUHIU UTHERI")
    c.restoreState()
    
    # Header
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height-55, "KARUHIU UTHERI - REPORT")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.drawString(50, height-75, f"Generated: {datetime.now().strftime('%d/%m/%Y')}")
    
    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    
    if report_type == 'farmer_produce':
        c.drawString(50, y, "Farmer Produce Report")
        y -= 30
        data = db.session.query(User.full_name, func.sum(Delivery.quantity)).join(
            Delivery, Delivery.farmer_id == User.id).filter(User.role == 'farmer').group_by(User.id).all()
        for name, qty in data:
            c.setFont("Helvetica", 10)
            c.drawString(60, y, f"{name}: {float(qty):.1f} kg")
            y -= 18
    
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                    download_name=f'Karuhiu_Utheri_Report_{datetime.now().strftime("%Y%m%d")}.pdf')

# ==================== PDF GENERATION ====================
def generate_pdf_statement(farmer_id):
    from reportlab.pdfgen import canvas
    
    farmer = db.session.get(User, farmer_id)
    payments = Payment.query.filter_by(farmer_id=farmer_id).order_by(
        Payment.payment_date.desc()).all()
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Watermark
    c.saveState()
    c.setFont("Helvetica-Bold", 80)
    c.setFillColorRGB(0.78, 0.66, 0.43, alpha=0.06)
    c.translate(width/2 - 200, height/2)
    c.rotate(45)
    c.drawString(-100, 0, "KARUHIU UTHERI")
    c.drawString(-50, -100, "COFFEE CO-OP")
    c.restoreState()
    
    c.saveState()
    c.setFont("Helvetica-Bold", 30)
    c.setFillColorRGB(0.78, 0.66, 0.43, alpha=0.04)
    for y in range(0, int(height), 120):
        for x in range(-50, int(width), 250):
            c.drawString(x, y, "☕ KU COFFEE")
    c.restoreState()
    
    # Header
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.setLineWidth(3)
    c.line(0, height - 120, width, height - 120)
    
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.circle(70, height - 60, 40, fill=True, stroke=False)
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(47, height - 72, "KU")
    c.setFont("Helvetica", 35)
    c.drawString(100, height - 80, "☕")
    
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(150, height - 55, "KARUHIU UTHERI")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.drawString(150, height - 75, "DIGITAL FARMERS COOPERATIVE SOCIETY")
    c.setFont("Helvetica", 8)
    c.drawString(150, height - 90, "Nyeri County, Kenya | Reg No: KCS/2024/8842")
    
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, height - 50, "PAYMENT STATEMENT")
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, height - 65, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(width - 40, height - 78, f"Ref: KU/PS/{farmer.id}/{datetime.now().strftime('%Y%m')}")
    
    # Farmer info
    y_start = height - 150
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.roundRect(40, y_start - 80, width - 80, 70, 10, fill=True, stroke=True)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, y_start - 35, f"Farmer: {farmer.full_name}")
    c.drawString(60, y_start - 52, f"Member No: {farmer.membership_number}")
    c.drawString(300, y_start - 35, f"Phone: {farmer.phone or 'N/A'}")
    c.drawString(300, y_start - 52, f"Email: {farmer.email or 'N/A'}")
    
    # Table
    y_pos = y_start - 110
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.rect(40, y_pos - 25, width - 80, 25, fill=True, stroke=False)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(1, 1, 1)
    for header, x in [('Date', 50), ('Gross Amount', 160), ('Deductions', 280),
                       ('Net Payment', 380), ('Status', 490), ('Receipt', 560)]:
        c.drawString(x, y_pos - 18, header)
    
    y_pos -= 40
    c.setFont("Helvetica", 8)
    total_gross = total_deductions = total_net = 0
    
    for i, payment in enumerate(payments):
        if y_pos < 120:
            c.showPage()
            y_pos = height - 50
        if i % 2 == 0:
            c.setFillColorRGB(0.97, 0.97, 0.97)
            c.rect(40, y_pos - 15, width - 80, 18, fill=True, stroke=False)
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(50, y_pos - 10, payment.payment_date.strftime('%d/%m/%Y'))
        c.drawString(160, y_pos - 10, f"KES {payment.amount_earned:,.2f}")
        c.drawString(280, y_pos - 10, f"KES {payment.deductions:,.2f}")
        c.drawString(380, y_pos - 10, f"KES {payment.net_payment:,.2f}")
        if payment.status == 'paid':
            c.setFillColorRGB(0.1, 0.6, 0.1)
            c.circle(495, y_pos - 5, 3, fill=True, stroke=False)
            c.drawString(502, y_pos - 10, "PAID")
        else:
            c.setFillColorRGB(0.8, 0.6, 0.1)
            c.circle(495, y_pos - 5, 3, fill=True, stroke=False)
            c.drawString(502, y_pos - 10, "PENDING")
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.drawString(560, y_pos - 10, f"RCT-{payment.id:06d}")
        total_gross += payment.amount_earned
        total_deductions += payment.deductions
        total_net += payment.net_payment
        y_pos -= 18
    
    # Totals
    y_pos -= 20
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.setLineWidth(2)
    c.line(40, y_pos + 10, width - 40, y_pos + 10)
    c.setFillColorRGB(0.95, 0.93, 0.88)
    c.roundRect(40, y_pos - 30, width - 80, 25, 8, fill=True, stroke=False)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(50, y_pos - 20, "TOTALS:")
    c.drawString(160, y_pos - 20, f"KES {total_gross:,.2f}")
    c.drawString(280, y_pos - 20, f"KES {total_deductions:,.2f}")
    c.drawString(380, y_pos - 20, f"KES {total_net:,.2f}")
    
    # Signatures
    y_pos -= 60
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.line(40, y_pos, 200, y_pos)
    c.drawString(40, y_pos - 15, "Farmer's Signature")
    c.line(380, y_pos, 550, y_pos)
    c.drawString(380, y_pos - 15, "Cooperative Secretary")
    c.setStrokeColorRGB(0.78, 0.66, 0.43)
    c.circle(width/2, y_pos - 10, 30, fill=False, stroke=True)
    c.setFont("Helvetica-Bold", 6)
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.drawString(width/2 - 25, y_pos - 13, "OFFICIAL")
    c.drawString(width/2 - 20, y_pos - 22, "STAMP")
    
    # Footer
    c.setFillColorRGB(0.09, 0.21, 0.12)
    c.rect(0, 0, width, 70, fill=True, stroke=False)
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.line(0, 70, width, 70)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.8, 0.8, 0.8)
    c.drawString(40, 50, "Official document from Karuhiu Utheri Digital Farmers Cooperative Society.")
    c.drawString(40, 38, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0.78, 0.66, 0.43)
    c.drawRightString(width - 40, 50, "☕ KARUHIU UTHERI DFC")
    
    c.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                    download_name=f'Karuhiu_Utheri_Statement_{farmer.full_name}_{datetime.now().strftime("%Y%m%d")}.pdf')

def generate_excel_statement(farmer_id):
    farmer = db.session.get(User, farmer_id)
    payments = Payment.query.filter_by(farmer_id=farmer_id).order_by(
        Payment.payment_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Amount Earned', 'Deductions', 'Net Payment', 'Status'])
    for p in payments:
        writer.writerow([p.payment_date.strftime('%Y-%m-%d'), p.amount_earned,
                        p.deductions, p.net_payment, p.status])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'statement_{farmer.full_name}_{datetime.now().date()}.csv')

# ==================== INIT ====================
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', full_name='System Administrator', role='admin',
                        membership_number='ADMIN001')
            admin.set_password('admin123')
            db.session.add(admin)
            staff = User(username='staff1', full_name='John Staff', role='staff',
                        membership_number='STAFF001')
            staff.set_password('staff123')
            db.session.add(staff)
            farmer = User(username='farmer1', full_name='Mike Farmer', role='farmer',
                         phone='+254712345678', membership_number='FARM001')
            farmer.set_password('farmer123')
            db.session.add(farmer)
            for grade, price in [('Premium', 5.50), ('A', 4.50), ('B', 3.50), ('C', 2.50)]:
                db.session.add(PriceConfig(quality_grade=grade, price_per_unit=price))
            db.session.commit()
            print("Database initialized!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
