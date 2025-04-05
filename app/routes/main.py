from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import requests
from .. import db
from ..models import User, Bookmark
from flask_mail import Mail, Message
from .. import mail, approval_email, password_reset_email, account_info_change_email
import re
from smtplib import SMTPAuthenticationError, SMTPServerDisconnected

main_bp = Blueprint('main', __name__)

# Valid themes
VALID_THEMES = ['cyberpunk', 'garnet_black', 'amethyst_abyss', 'quantum_blue']

# Basic email validation function
def validate_email_address(email):
    if not email:
        return False
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def check_url_status(url):
    if not url:
        return False
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            print(f"HEAD success for {url}: {response.status_code}")
            return True
        else:
            print(f"HEAD failed for {url}: {response.status_code}")
            response = requests.get(url, timeout=5, allow_redirects=True)
            print(f"GET result for {url}: {response.status_code}")
            return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error checking {url}: {str(e)}")
        return False

@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def bookmarks():
    if request.method == 'POST':
        if 'add_bookmark' in request.form:
            name = request.form['name']
            server_url = request.form.get('server_url') or None
            domain_url = request.form.get('domain_url') or None
            image_url = request.form.get('image_link') or None
            
            if 'image_upload' in request.files and request.files['image_upload'].filename:
                file = request.files['image_upload']
                filename = secure_filename(file.filename)
                filename = f"{os.urandom(8).hex()}-{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                image_url = f"/static/images/{filename}"
            
            bookmark = Bookmark(user_id=current_user.id, name=name, server_url=server_url, domain_url=domain_url, image_url=image_url)
            db.session.add(bookmark)
            db.session.commit()
            return redirect(url_for('main.bookmarks'))
        
        if 'edit_bookmark' in request.form:
            bookmark_id = request.form['bookmark_id']
            bookmark = Bookmark.query.get_or_404(bookmark_id)
            if bookmark.user_id != current_user.id:
                flash('Unauthorized action.', 'error')
                return redirect(url_for('main.bookmarks'))
            
            bookmark.name = request.form['name']
            bookmark.server_url = request.form.get('server_url') or None
            bookmark.domain_url = request.form.get('domain_url') or None
            
            if request.form.get('image_link'):
                bookmark.image_url = request.form['image_link']
            elif 'image_upload' in request.files and request.files['image_upload'].filename:
                file = request.files['image_upload']
                filename = secure_filename(file.filename)
                filename = f"{os.urandom(8).hex()}-{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                bookmark.image_url = f"/static/images/{filename}"
            
            db.session.commit()
            return redirect(url_for('main.bookmarks'))
    
    if 'delete' in request.args:
        bookmark_id = request.args.get('delete')
        bookmark = Bookmark.query.get_or_404(bookmark_id)
        if bookmark.user_id == current_user.id:
            if bookmark.image_url and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], bookmark.image_url.split('/')[-1])):
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], bookmark.image_url.split('/')[-1]))
            db.session.delete(bookmark)
            db.session.commit()
        return redirect(url_for('main.bookmarks'))
    
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    for bookmark in bookmarks:
        bookmark.server_status = check_url_status(bookmark.server_url)
        bookmark.domain_status = check_url_status(bookmark.domain_url)
    return render_template('bookmarks.html', bookmarks=bookmarks, display_name=current_user.real_name or current_user.username)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'theme' in request.form and 'update_profile' not in request.form:
            new_theme = request.form['theme']
            if new_theme in VALID_THEMES:
                current_user.theme = new_theme
                session['theme'] = new_theme
                db.session.commit()
                flash('Theme updated successfully!', 'success')
            return redirect(url_for('main.profile'))

        if 'update_profile' in request.form:
            current_password = request.form.get('current_password')
            if not current_password or not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect or missing!', 'error')
            else:
                updated = False
                changes = {}
                if request.form['real_name'] != (current_user.real_name or ''):
                    current_user.real_name = request.form['real_name']
                    changes['name'] = current_user.real_name
                    flash('Name updated successfully!', 'success')
                    updated = True
                if request.form['new_username'] != current_user.username:
                    if User.query.filter_by(username=request.form['new_username']).first():
                        flash('Username already taken!', 'error')
                    else:
                        current_user.username = request.form['new_username']
                        changes['username'] = current_user.username
                        flash('Username updated successfully!', 'success')
                        updated = True
                if request.form['email'] != (current_user.email or ''):
                    if not validate_email_address(request.form['email']):
                        flash('Invalid email address.', 'error')
                        return redirect(url_for('main.profile'))
                    # Check for email uniqueness
                    if User.query.filter(User.email == request.form['email'], User.id != current_user.id).first():
                        flash('Email already in use by another account.', 'error')
                        return redirect(url_for('main.profile'))
                    current_user.email = request.form['email']
                    changes['email'] = current_user.email
                    flash('Email updated successfully!', 'success')
                    updated = True
                if request.form['new_password'] and request.form['new_password'] == request.form['confirm_password']:
                    current_user.password = generate_password_hash(request.form['new_password'])
                    changes['password'] = True
                    flash('Password updated successfully!', 'success')
                    updated = True

                if updated:
                    db.session.commit()
                    if changes and current_user.email:
                        msg = Message("Account Information Updated", recipients=[current_user.email])
                        msg.html = account_info_change_email(current_user.real_name or current_user.username, changes)
                        try:
                            with current_app.app_context():
                                mail.send(msg)
                            flash('A confirmation email has been sent with your updated information.', 'success')
                        except SMTPAuthenticationError:
                            flash('Failed to send confirmation email due to authentication error.', 'warning')
                            print("Email sending error: SMTP authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
                        except SMTPServerDisconnected:
                            flash('Failed to send confirmation email due to server connection issue.', 'warning')
                            print("Email sending error: SMTP server disconnected. Check network or MAIL_SERVER settings.")
                        except Exception as e:
                            flash('Failed to send confirmation email.', 'warning')
                            print(f"Email sending error: {str(e)}")
                    return render_template('info_change.html', changes=changes)
                else:
                    flash('No changes detected.', 'info')
            return redirect(url_for('main.profile'))

    return render_template('profile.html', user=current_user)

@main_bp.route('/admin_panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Only admins can access this page.', 'error')
        return render_template('access_denied.html')
    
    if request.method == 'POST':
        if 'approve' in request.form:
            user_id = request.form['approve']
            user = User.query.get_or_404(user_id)
            user.status = 'approved'
            db.session.commit()
            if user.email and validate_email_address(user.email):
                msg = Message("Account Approved", recipients=[user.email])
                msg.html = approval_email(user.real_name or user.username, user.username)
                try:
                    with current_app.app_context():
                        mail.send(msg)
                    flash(f"User {user.username} approved! A confirmation email has been sent.", 'success')
                except SMTPAuthenticationError:
                    flash(f"User {user.username} approved, but failed to send confirmation email due to authentication error.", 'warning')
                    print("Email sending error: SMTP authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
                except SMTPServerDisconnected:
                    flash(f"User {user.username} approved, but failed to send confirmation email due to server connection issue.", 'warning')
                    print("Email sending error: SMTP server disconnected. Check network or MAIL_SERVER settings.")
                except Exception as e:
                    flash(f"User {user.username} approved, but failed to send confirmation email.", 'warning')
                    print(f"Email sending error: {str(e)}")
            else:
                flash(f"User {user.username} approved! No valid email provided to send confirmation.", 'success')
        
        elif 'deny' in request.form:
            user_id = request.form['deny']
            user = User.query.get_or_404(user_id)
            user.status = 'denied'
            db.session.commit()
            flash(f"User {user.username} denied!", 'success')
        
        elif 'delete' in request.form:
            user_id = request.form['delete']
            user = User.query.get_or_404(user_id)
            if user.username == current_user.username:
                flash('You cannot delete your own account!', 'error')
            else:
                # Delete the user's bookmarks first
                bookmarks = Bookmark.query.filter_by(user_id=user.id).all()
                for bookmark in bookmarks:
                    if bookmark.image_url and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], bookmark.image_url.split('/')[-1])):
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], bookmark.image_url.split('/')[-1]))
                    db.session.delete(bookmark)
                # Now delete the user
                db.session.delete(user)
                db.session.commit()
                flash(f"User {user.username} deleted!", 'success')
        
        elif 'reset_password' in request.form:
            user_id = request.form['reset_password']
            user = User.query.get_or_404(user_id)
            new_password = 'ChangeMe123@'  # Consistent with email
            user.password = generate_password_hash(new_password)
            db.session.commit()
            if user.email and validate_email_address(user.email):
                msg = Message("Password Reset", recipients=[user.email])
                msg.html = password_reset_email(user.real_name or user.username, user.username, new_password)
                try:
                    with current_app.app_context():
                        mail.send(msg)
                    flash(f"Password for {user.username} reset to '{new_password}'! A confirmation email has been sent.", 'success')
                except SMTPAuthenticationError:
                    flash(f"Password for {user.username} reset to '{new_password}', but failed to send confirmation email due to authentication error.", 'warning')
                    print("Email sending error: SMTP authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD.")
                except SMTPServerDisconnected:
                    flash(f"Password for {user.username} reset to '{new_password}', but failed to send confirmation email due to server connection issue.", 'warning')
                    print("Email sending error: SMTP server disconnected. Check network or MAIL_SERVER settings.")
                except Exception as e:
                    flash(f"Password for {user.username} reset to '{new_password}', but failed to send confirmation email.", 'warning')
                    print(f"Email sending error: {str(e)}")
            else:
                flash(f"Password for {user.username} reset to '{new_password}'! No valid email provided to send confirmation.", 'success')
        
        elif 'role' in request.form:
            user_id = request.form['user_id']
            user = User.query.get_or_404(user_id)
            new_role = request.form['role']
            if new_role in ['user', 'admin']:
                if user.username == current_user.username and new_role != 'admin':
                    flash('You cannot demote yourself from admin!', 'error')
                else:
                    user.role = new_role
                    db.session.commit()
                    flash(f"Role for {user.username} updated to {new_role}!", 'success')
    
    pending_users = User.query.filter_by(status='pending').all()
    approved_users = User.query.filter_by(status='approved').filter(User.id != current_user.id).all()
    return render_template('admin_panel.html', pending_users=pending_users, approved_users=approved_users)

@main_bp.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')