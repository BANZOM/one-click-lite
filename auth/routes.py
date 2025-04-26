from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .user import User # Use relative import within the blueprint package
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, template_folder='../templates') # Point to root templates

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them away from login page
    if current_user.is_authenticated:
         return redirect(url_for('home')) # Redirect to main dashboard

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if not username or not password:
            flash('Username and password are required.', 'warning')
            return redirect(url_for('auth.login'))

        user = User.get(username)

        # Check if user exists and password is correct
        if user and user.check_password(password):
            login_user(user, remember=remember)
            logger.info(f"User '{username}' logged in successfully.")
            # Redirect to the page user tried to access, or home page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            logger.warning(f"Failed login attempt for username: '{username}'")
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))

    # For GET request, just show the login page
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required # Must be logged in to log out
def logout():
    logger.info(f"User '{current_user.id}' logged out.")
    logout_user()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('auth.login')) # Redirect to login page after logout