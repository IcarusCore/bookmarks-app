from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .models import db, User
import os
import secrets

# Initialize extensions
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))

    # Database setup
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'bookmarks.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/images')

    # Flask-Mail configuration using environment variables without defaults
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')  # No default
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT')) if os.getenv('MAIL_PORT') else None  # Convert to int if provided
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'  # Default to False if not set
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'  # Default to False if not set
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # No default
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # No default
    app.config['MAIL_DEFAULT_SENDER'] = (
        os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Noreply - Bookmarks'),  # Default name only
        os.getenv('MAIL_USERNAME')  # Email tied to username, no default
    ) if os.getenv('MAIL_USERNAME') else None  # Set to None if no username
    app.config['MAIL_ASCII_ATTACHMENTS'] = os.getenv('MAIL_ASCII_ATTACHMENTS', 'False').lower() == 'true'
    app.config['MAIL_CHARSET'] = os.getenv('MAIL_CHARSET', 'UTF-8')

    # Initialize extensions with the app
    db.init_app(app)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    from .routes.auth import auth_bp
    from .routes.main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

# Email template functions
def generate_email_html(subject, body_content):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{subject}</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
            <tr>
                <td align="center">
                    <table width="600px" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="background-color: #1b263b; color: #00ffff; text-align: center; padding: 20px; border-top-left-radius: 8px; border-top-right-radius: 8px;">
                                <h1 style="margin: 0; font-size: 24px; text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);">{subject}</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; color: #333333; line-height: 1.6;">
                                <div style="background-color: #f9f9f9; border: 1px solid #00ffff; border-radius: 5px; padding: 15px; box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);">
                                    {body_content}
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align: center; padding: 10px; color: #777777; font-size: 12px; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                                <p style="margin: 0;">© 2025 Bookmarks. All rights reserved. 
                                <!-- Optional: Add Privacy Policy link if your email client supports it -->
                                <!-- <a href="https://yourdomain.com/privacy-policy" style="color: #00ffff; text-decoration: none;">Privacy Policy</a> -->
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def registration_email(name):
    body = f"""
    <p>Hello {name},</p>
    <p>Thank you for registering! Your account is pending approval.</p>
    <p>Thank you,<br>Management</p>
    """
    return generate_email_html("Registration Confirmation", body)

def approval_email(name, username):
    body = f"""
    <p>Hello {name},</p>
    <p>Thank you for registering! Your account has been approved! You may login now.</p>
    <p><strong>Username:</strong> {username}</p>
    <p>Thank you,<br>Management</p>
    """
    return generate_email_html("Account Approved", body)

def password_reset_email(name, username, temp_password="ChangeMe123@"):
    body = f"""
    <p>Hello {name},</p>
    <p>Your password has been reset. Below is your new information, please update your password in your profile section within 24 hours!</p>
    <p><strong>Username:</strong> {username}</p>
    <p><strong>Password:</strong> {temp_password}</p>
    <p>Thank you,<br>Management</p>
    """
    return generate_email_html("Password Reset", body)

def account_info_change_email(name, changes):
    body_lines = [f"<p>Hello {name},</p>", "<p>Your account information has been updated.</p>"]
    if "name" in changes:
        body_lines.append(f"<p><strong>Name:</strong> {changes['name']}</p>")
    if "email" in changes:
        body_lines.append(f"<p><strong>Email:</strong> {changes['email']}</p>")
    if "username" in changes:
        body_lines.append(f"<p><strong>Username:</strong> {changes['username']}</p>")
    if "password" in changes:
        body_lines.append(f"<p><strong>Password:</strong> changed</p>")
    body_lines.append("<p>Thank you,<br>Management</p>")
    body = "".join(body_lines)
    return generate_email_html("Account Information Updated", body)