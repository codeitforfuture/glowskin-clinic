import os
import random
import string
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database import get_db_connection, init_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

CLINIC = {
    'name': 'GlowSkin',
    'tagline': 'Radiant skin. Expert care. Timeless beauty.',
    'phone': '+1 (555) 123-4567',
    'email': 'hello@glowskin.clinic',
    'address': '123 Serenity Lane, Beverly Hills, CA 90210',
    'hours': 'Mon–Sat: 9:00 AM – 6:00 PM',
    'established': 2015
}

SERVICES = [
    {'name': 'Signature Glow Facial', 'price': 120, 'duration': '60 min', 'category': 'Facial',
     'description': 'Our signature deep-cleansing facial with premium botanical extracts for instant radiance.', 'icon': '✨'},
    {'name': 'Skin Consultation', 'price': 75, 'duration': '30 min', 'category': 'Consultation',
     'description': 'A personalized one-on-one skin analysis with a tailored treatment roadmap.', 'icon': '🔍'},
    {'name': 'Chemical Peel', 'price': 150, 'duration': '45 min', 'category': 'Advanced',
     'description': 'Medical-grade peel that targets fine lines, acne scars, and uneven tone.', 'icon': '💧'},
    {'name': 'Microdermabrasion', 'price': 130, 'duration': '45 min', 'category': 'Advanced',
     'description': 'Gentle exfoliation that smooths texture, unclogs pores, and boosts collagen.', 'icon': '🌟'},
    {'name': 'LED Light Therapy', 'price': 95, 'duration': '30 min', 'category': 'Therapy',
     'description': 'Non-invasive light treatment for acne, inflammation, and anti-aging.', 'icon': '💡'},
    {'name': 'Dermaplaning', 'price': 110, 'duration': '40 min', 'category': 'Facial',
     'description': 'Removes peach fuzz and dead skin cells for a flawless, smooth canvas.', 'icon': '🌸'},
    {'name': 'Hydrafacial Deluxe', 'price': 180, 'duration': '75 min', 'category': 'Facial',
     'description': 'Multi-step hydradermabrasion that cleanses, extracts, and hydrates.', 'icon': '💎'},
    {'name': 'Anti-Aging Ritual', 'price': 200, 'duration': '90 min', 'category': 'Advanced',
     'description': 'Complete anti-aging protocol with peptides, serums, and LED therapy.', 'icon': '🌹'},
]

TIME_SLOTS = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30', '17:00', '17:30'
]

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')


def get_service_price(service_name):
    for s in SERVICES:
        if s['name'] == service_name:
            return s['price']
    return 0


def generate_reference():
    return 'GS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to view your bookings.', 'error')
            return redirect(url_for('user_login', next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_globals():
    current_user = None
    if session.get('user_id'):
        conn = get_db_connection()
        current_user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        # 🚨 If user no longer exists, clear the stale session
        if not current_user:
            session.pop('user_id', None)
    return dict(
        clinic=CLINIC,
        current_year=datetime.now().year,
        now=datetime.now(),
        timedelta=timedelta,
        current_user=current_user
    )


# ---------------- PUBLIC ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html', services=SERVICES[:6])


@app.route('/services')
def services():
    categories = sorted(set(s['category'] for s in SERVICES))
    return render_template('services.html', services=SERVICES, categories=categories)


@app.route('/about')
def about():
    return render_template('about.html')


# ---------------- USER AUTH ----------------
@app.route('/signup', methods=['GET', 'POST'])
def user_signup():
    if session.get('user_id'):
        return redirect(url_for('my_bookings'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        errors = []
        if not name: errors.append('Name is required.')
        if not email or '@' not in email: errors.append('Valid email is required.')
        if not phone: errors.append('Phone is required.')
        if len(password) < 6: errors.append('Password must be at least 6 characters.')
        if password != confirm: errors.append('Passwords do not match.')

        if not errors:
            conn = get_db_connection()
            existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                errors.append('An account with this email already exists.')
            else:
                conn.execute(
                    'INSERT INTO users (name, email, phone, password_hash) VALUES (?, ?, ?, ?)',
                    (name, email, phone, generate_password_hash(password))
                )
                conn.commit()
                user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
                conn.close()
                session['user_id'] = user['id']
                flash(f'Welcome, {name}! Your account is ready.', 'success')
                return redirect(url_for('my_bookings'))
            conn.close()

        for e in errors:
            flash(e, 'error')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if session.get('user_id'):
        return redirect(url_for('my_bookings'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            flash(f'Welcome back, {user["name"]}!', 'success')
            next_url = request.args.get('next') or url_for('my_bookings')
            return redirect(next_url)
        flash('Invalid email or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def user_logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# ---------------- BOOKING ----------------
@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    # Pre-fill for logged in user
    current_user = None
    if session.get('user_id'):
        conn = get_db_connection()
        current_user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
    

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        service = request.form.get('service', '').strip()
        appointment_date = request.form.get('date', '').strip()
        appointment_time = request.form.get('time', '').strip()
        notes = request.form.get('notes', '').strip()

        errors = []
        if not name: errors.append('Full name is required.')
        if not phone: errors.append('Phone number is required.')
        if not service or service not in [s['name'] for s in SERVICES]:
            errors.append('Please select a valid service.')
        if not appointment_date:
            errors.append('Please select a date.')
        else:
            try:
                d = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                if d < date.today(): errors.append('Appointment date cannot be in the past.')
                if d.weekday() == 6: errors.append('We are closed on Sundays.')
                if d > date.today() + timedelta(days=90):
                    errors.append('Bookings are limited to 90 days in advance.')
            except ValueError:
                errors.append('Invalid date format.')
        if not appointment_time or appointment_time not in TIME_SLOTS:
            errors.append('Please select a valid time slot.')

        if errors:
            for e in errors: flash(e, 'error')
            return render_template('booking.html', services=SERVICES, time_slots=TIME_SLOTS, form_data=request.form)

        conn = get_db_connection()
        try:
            ref = generate_reference()
            user_id = session.get('user_id')
            conn.execute(
                '''INSERT INTO appointments 
                   (reference_code, user_id, name, phone, email, service, appointment_date, appointment_time, notes, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (ref, user_id, name, phone, email, service, appointment_date, appointment_time, notes, 'pending')
            )
            conn.commit()
            flash(f'✅ Booking request received! Your reference code is {ref}. We will confirm shortly.', 'success')
            return redirect(url_for('booking'))
        except Exception as e:
            print(f"❌ DB ERROR: {e}")
            flash('Something went wrong. Please try again.', 'error')
            return render_template('booking.html', services=SERVICES, time_slots=TIME_SLOTS, form_data=request.form)
        finally:
            conn.close()

    return render_template('booking.html', services=SERVICES, time_slots=TIME_SLOTS, form_data={})


@app.route('/my-bookings')
def my_bookings():
    if session.get('user_id'):
        conn = get_db_connection()
        appointments = conn.execute(
            'SELECT * FROM appointments WHERE user_id = ? ORDER BY appointment_date DESC, appointment_time DESC',
            (session['user_id'],)
        ).fetchall()
        conn.close()
        return render_template('my_bookings.html', appointments=appointments, logged_in=True)

    # Guest lookup by reference code
    appointment = None
    search_term = ''
    searched = False
    if request.args.get('ref'):
        search_term = request.args.get('ref', '').strip().upper()
        searched = True
        if search_term:
            conn = get_db_connection()
            appointment = conn.execute(
                'SELECT * FROM appointments WHERE reference_code = ?', (search_term,)
            ).fetchone()
            conn.close()
            if not appointment:
                flash('No booking found with that reference code.', 'error')

    return render_template('my_bookings.html',
                           appointment=appointment,
                           search_term=search_term,
                           searched=searched,
                           logged_in=False)


@app.route('/cancel-booking/<int:appointment_id>', methods=['POST'])
def cancel_booking(appointment_id):
    conn = get_db_connection()
    appt = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
    if not appt:
        flash('Booking not found.', 'error')
        conn.close()
        return redirect(url_for('my_bookings'))

    # Security: only owner or admin can cancel
    if not (session.get('admin_logged_in') or (session.get('user_id') and appt['user_id'] == session['user_id'])):
        flash('You cannot cancel this booking.', 'error')
        conn.close()
        return redirect(url_for('my_bookings'))

    if appt['status'] in ['pending', 'confirmed']:
        conn.execute('UPDATE appointments SET status = "cancelled" WHERE id = ?', (appointment_id,))
        conn.commit()
        flash('Your appointment has been cancelled.', 'success')
    else:
        flash('This booking cannot be cancelled.', 'error')
    conn.close()
    return redirect(url_for('my_bookings'))


@app.route('/api/availability')
def availability():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    conn = get_db_connection()
    booked = conn.execute(
        'SELECT appointment_time FROM appointments WHERE appointment_date = ? AND status != "cancelled"',
        (date_str,)
    ).fetchall()
    conn.close()
    booked_times = {row['appointment_time'] for row in booked}
    available = [t for t in TIME_SLOTS if t not in booked_times]
    return jsonify({'available': available, 'booked': list(booked_times)})


# ---------------- ADMIN ROUTES ----------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Admin logged out.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    status_filter = request.args.get('status', 'all')
    search = request.args.get('q', '').strip()

    conn = get_db_connection()

    # --- Filtered appointments ---
    query = 'SELECT * FROM appointments WHERE 1=1'
    params = []
    if status_filter != 'all':
        query += ' AND status = ?'
        params.append(status_filter)
    if search:
        query += ' AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR reference_code LIKE ?)'
        like = f'%{search}%'
        params.extend([like, like, like, like])
    query += ' ORDER BY appointment_date DESC, appointment_time DESC'
    appointments = conn.execute(query, params).fetchall()

    # --- Stats ---
    today = date.today().strftime('%Y-%m-%d')
    stats = {
        'today': conn.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status != "cancelled"', (today,)).fetchone()[0],
        'pending': conn.execute('SELECT COUNT(*) FROM appointments WHERE status = "pending"').fetchone()[0],
        'confirmed': conn.execute('SELECT COUNT(*) FROM appointments WHERE status = "confirmed"').fetchone()[0],
        'completed': conn.execute('SELECT COUNT(*) FROM appointments WHERE status = "completed"').fetchone()[0],
        'cancelled': conn.execute('SELECT COUNT(*) FROM appointments WHERE status = "cancelled"').fetchone()[0],
        'total': conn.execute('SELECT COUNT(*) FROM appointments').fetchone()[0],
        'total_users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
    }

    # --- Revenue from completed ---
    completed_appts = conn.execute('SELECT service FROM appointments WHERE status = "completed"').fetchall()
    stats['revenue'] = sum(get_service_price(row['service']) for row in completed_appts)

    # --- Today's schedule ---
    today_schedule = conn.execute(
        'SELECT * FROM appointments WHERE appointment_date = ? AND status != "cancelled" ORDER BY appointment_time',
        (today,)
    ).fetchall()

    # --- Analytics: last 7 days (revenue + count) ---
    last_7_days = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_appts = conn.execute(
            'SELECT service FROM appointments WHERE appointment_date = ? AND status != "cancelled"',
            (d,)
        ).fetchall()
        day_revenue = sum(get_service_price(a['service']) for a in day_appts)
        last_7_days.append({
            'date': d,
            'label': datetime.strptime(d, '%Y-%m-%d').strftime('%a'),
            'count': len(day_appts),
            'revenue': day_revenue
        })

    # --- Top services ---
    top_rows = conn.execute('''
        SELECT service, COUNT(*) as cnt FROM appointments 
        WHERE status != "cancelled" 
        GROUP BY service ORDER BY cnt DESC LIMIT 5
    ''').fetchall()
    top_services = [{'name': r['service'], 'count': r['cnt']} for r in top_rows]

    conn.close()

    analytics = {
        'labels': [d['label'] for d in last_7_days],
        'revenues': [d['revenue'] for d in last_7_days],
        'counts': [d['count'] for d in last_7_days],
        'status_counts': [stats['pending'], stats['confirmed'], stats['completed'], stats['cancelled']],
        'top_services': top_services
    }

    return render_template('admin/dashboard.html',
                           appointments=appointments,
                           stats=stats,
                           today_schedule=today_schedule,
                           status_filter=status_filter,
                           search=search,
                           analytics=analytics)


@app.route('/admin/update_status/<int:appointment_id>', methods=['POST'])
@admin_required
def update_status(appointment_id):
    new_status = request.form.get('status')
    if new_status not in ['pending', 'confirmed', 'completed', 'cancelled']:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin_dashboard'))
    conn = get_db_connection()
    conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (new_status, appointment_id))
    conn.commit()
    conn.close()
    flash('Status updated.', 'success')
    return redirect(url_for('admin_dashboard'))


init_db()

if __name__ == '__main__':
    app.run(debug=True)