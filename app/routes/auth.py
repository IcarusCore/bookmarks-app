from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db
from ..models import User
from flask_mail import Mail, Message
from .. import mail, registration_email
import re
from smtplib import SMTPAuthenticationError, SMTPServerDisconnected

auth_bp = Blueprint('auth', __name__)

# Basic email validation function
def validate_email_address(email):
    if not email:
        return False
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

# Password validation function
def validate_password(password):
    if len(password) < 8:
        return False
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.status == 'approved':
                login_user(user)
                session['theme'] = user.theme
                return redirect(url_for('main.bookmarks'))
            else:
                flash('Your account is pending approval or has been denied.', 'error')
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        real_name = request.form['real_name']
        email = request.form['email']
        
        # Check for existing username or email
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already in use', 'error')
        elif not validate_email_address(email):
            flash('Invalid email address.', 'error')
        elif not validate_password(password):
            flash('Password must be at least 8 characters long.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            is_first_user = User.query.count() == 0
            new_user = User(
                username=username,
                password=hashed_password,
                real_name=real_name,
                email=email,
                role='admin' if is_first_user else 'user',
                status='approved' if is_first_user else 'pending'
            )
            db.session.add(new_user)
            db.session.commit()

            if not is_first_user:  # Only send email for non-admin users
                msg = Message("Registration Confirmation", recipients=[email])
                msg.html = registration_email(real_name or username)
                try:
                    with current_app.app_context():
                        mail.send(msg)
                    flash('Registration submitted! Awaiting admin approval. A confirmation email has been sent.', 'success')
                except SMTPAuthenticationError:
                    flash('Registration submitted! Awaiting admin approval. Failed to send confirmation email due to authentication error.', 'warning')
                    print("Email sending error: SMTP authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
                except SMTPServerDisconnected:
                    flash('Registration submitted! Awaiting admin approval. Failed to send confirmation email due to server connection issue.', 'warning')
                    print("Email sending error: SMTP server disconnected. Check network or MAIL_SERVER settings.")
                except Exception as e:
                    flash('Registration submitted! Awaiting admin approval. Failed to send confirmation email.', 'warning')
                    print(f"Email sending error: {str(e)}")
            else:
                flash('Admin account created! Please log in.', 'success')

            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('theme', None)
    return redirect(url_for('auth.login'))