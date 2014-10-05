""" This file contains view functions for Flask-User forms.

    :copyright: (c) 2013 by Ling Thio
    :author: Ling Thio (ling.thio@gmail.com)
    :license: Simplified BSD License, see LICENSE.txt for more details."""

from datetime import datetime
from flask import current_app, flash, redirect, render_template, request, url_for
from flask.ext.login import current_user, login_user, logout_user
from .decorators import login_required
from . import emails
from . import signals
from .translations import gettext as _
import sys

# Handle Python 2.x and Python 3.x
try:
    from urllib.parse import quote      # Python 3.x
except ImportError:
    from urllib import quote            # Python 2.x

def confirm_email(token):
    """ Verify email confirmation token and activate the user account."""
    # Verify token
    user_manager = current_app.user_manager
    db_adapter = user_manager.db_adapter
    is_valid, has_expired, object_id = user_manager.verify_token(
            token,
            user_manager.confirm_email_expiration)

    if has_expired:
        flash(_('Your confirmation token has expired.'), 'error')
        return redirect(url_for('user.login'))

    if not is_valid:
        flash(_('Invalid confirmation token.'), 'error')
        return redirect(url_for('user.login'))

    # Confirm email by setting User.active=True and User.confirmed_at=utcnow()
    if db_adapter.UserEmailClass:
        user_email = user_manager.get_user_email_by_id(object_id)
        if user_email:
            user_email.confirmed_at = datetime.utcnow()
            user = user_email.user
        else:
            user = None
    else:
        user_email = None
        user = user_manager.get_user_by_id(object_id)
        user.confirmed_at = datetime.utcnow()

    if user:
        user.active = True
        db_adapter.commit()
    else:                                               # pragma: no cover
        flash(_('Invalid confirmation token.'), 'error')
        return redirect(url_for('user.login'))

    # Send email_confirmed signal
    signals.user_confirmed_email.send(current_app._get_current_object(), user=user)

    # Prepare one-time system message
    flash(_('Your email has been confirmed.'), 'success')

    # Redirect to login page or auto-login if configured
    next = request.args.get('next', _endpoint_url(user_manager.after_confirm_endpoint))
    if user_manager.auto_login_after_confirm:
        return _do_login_user(user, next)  # Auto-login user after confirm
    else:
        return redirect(url_for('user.login')+'?next='+next)


@login_required
def change_password():
    """ Prompt for old password and new password and change the user's password."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Initialize form
    form = user_manager.change_password_form(request.form)
    form.next.data = request.args.get('next', _endpoint_url(user_manager.after_change_password_endpoint))  # Place ?next query param in next form field

    # Process valid POST
    if request.method=='POST' and form.validate():
        # Hash password
        hashed_password = user_manager.hash_password(form.new_password.data)

        # Change password
        db_adapter.update_object(current_user, password=hashed_password)
        db_adapter.commit()

        # Send 'password_changed' email
        if user_manager.enable_email and user_manager.send_password_changed_email:
            emails.send_password_changed_email(current_user)

        # Send password_changed signal
        signals.user_changed_password.send(current_app._get_current_object(), user=current_user)

        # Prepare one-time system message
        flash(_('Your password has been changed successfully.'), 'success')

        # Redirect to 'next' URL
        return redirect(form.next.data)

    # Process GET or invalid POST
    return render_template(user_manager.change_password_template, form=form)

@login_required
def change_username():
    """ Prompt for new username and old password and change the user's username."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Initialize form
    form = user_manager.change_username_form(request.form)
    form.next.data = request.args.get('next', _endpoint_url(user_manager.after_change_username_endpoint))  # Place ?next query param in next form field

    # Process valid POST
    if request.method=='POST' and form.validate():
        new_username = form.new_username.data

        # Change username
        db_adapter.update_object(current_user, username=new_username)
        db_adapter.commit()

        # Send 'username_changed' email
        if user_manager.enable_email and user_manager.send_username_changed_email:
            emails.send_username_changed_email(current_user)

        # Send username_changed signal
        signals.user_changed_username.send(current_app._get_current_object(), user=current_user)

        # Prepare one-time system message
        flash(_("Your username has been changed to '%(username)s'.", username=new_username), 'success')

        # Redirect to 'next' URL
        return redirect(form.next.data)

    # Process GET or invalid POST
    return render_template(user_manager.change_username_template, form=form)

@login_required
def email_action(id, action):
    """ Perform action 'action' on UserEmail object 'id'
    """
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Retrieve UserEmail by id
    user_email = db_adapter.find_first_object(db_adapter.UserEmailClass, id=id)

    # Users may only change their own UserEmails
    if not user_email or user_email.user_id != int(current_user.get_id()):
        return unauthorized()

    if action=='delete':
        # Primary UserEmail can not be deleted
        if user_email.is_primary:
            return unauthorized()
        # Delete UserEmail
        db_adapter.delete_object(user_email)
        db_adapter.commit()

    elif action=='make-primary':
        # Disable previously primary emails
        user_emails = db_adapter.find_all_objects(db_adapter.UserEmailClass, user_id=int(current_user.get_id()))
        for ue in user_emails:
            if ue.is_primary:
                ue.is_primary = False
        # Enable current primary email
        user_email.is_primary = True
        # Commit
        db_adapter.commit()

    elif action=='confirm':
        _send_confirm_email(user_email.user, user_email)

    else:
        return unauthorized()

    return redirect(url_for('user.manage_emails'))

def forgot_password():
    """Prompt for email and send reset password email."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Initialize form
    form = user_manager.forgot_password_form(request.form)

    # Process valid POST
    if request.method=='POST' and form.validate():
        email = form.email.data

        # Find user by email
        user, user_email = user_manager.find_user_by_email(email)
        if user:
            # Generate reset password link
            token = user_manager.generate_token(int(user.get_id()))
            reset_password_link = url_for('user.reset_password', token=token, _external=True)

            # Send forgot password email
            emails.send_forgot_password_email(user, user_email, reset_password_link)

            # Store token
            if hasattr(user, 'reset_password_token'):
                db_adapter.update_object(user, reset_password_token=token)
                db_adapter.commit()

            # Send forgot_password signal
            signals.user_forgot_password.send(current_app._get_current_object(), user=user)

        # Prepare one-time system message
        flash(_("A reset password email has been sent to '%(email)s'. Open that email and follow the instructions to reset your password.", email=email), 'success')

        # Redirect to the login page
        return redirect(_endpoint_url(user_manager.after_forgot_password_endpoint))

    # Process GET or invalid POST
    return render_template(user_manager.forgot_password_template, form=form)


def login():
    """ Prompt for username/email and password and sign the user in."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    next = request.args.get('next', _endpoint_url(user_manager.after_login_endpoint))
    reg_next = request.args.get('reg_next', _endpoint_url(user_manager.after_register_endpoint))

    # Immediately redirect already logged in users
    if current_user.is_authenticated() and user_manager.auto_login_at_login:
        return redirect(next)

    # Initialize form
    login_form = user_manager.login_form(request.form)          # for login.html
    register_form = user_manager.register_form()                # for login_or_register.html
    if request.method!='POST':
        login_form.next.data     = register_form.next.data = next
        login_form.reg_next.data = register_form.reg_next.data = reg_next

    # Process valid POST
    if request.method=='POST' and login_form.validate():
        # Retrieve User
        user_email = None
        if user_manager.enable_username:
            # Find user by username or email address
            user = user_manager.find_user_by_username(login_form.username.data)
            user_email = None
            if user and db_adapter.UserEmailClass:
                user_email = db_adapter.find_first_object(db_adapter.UserEmailClass,
                        user_id=int(user.get_id()),
                        is_primary=True,
                        )
            if not user and user_manager.enable_email:
                user, user_email = user_manager.find_user_by_email(login_form.username.data)
        else:
            # Find user by email address
            user, user_email = user_manager.find_user_by_email(login_form.email.data)

        if user:
            if user.active:
                return _do_login_user(user, login_form.next.data, login_form.remember_me.data)  # Login user after Login
            else:
                confirmed_at = user_email.confirmed_at if user_email else user.confirmed_at
                if user_manager.enable_confirm_email and not confirmed_at:
                    url = url_for('user.resend_confirm_email')
                    flash(_('Your email address has not yet been confirmed. Check your email Inbox and Spam folders for the confirmation email or <a href="%(url)s">Re-send confirmation email</a>.', url=url), 'error')
                else:
                    flash(_('Your account has been disabled.'), 'error')
                return redirect(url_for('user.home'))

    # Process GET or invalid POST
    return render_template(user_manager.login_template,
            form=login_form,
            login_form=login_form,
            register_form=register_form)

def logout():
    """ Sign the user out."""
    user_manager =  current_app.user_manager

    # Send user_logged_out signal
    signals.user_logged_out.send(current_app._get_current_object(), user=current_user)

    # Use Flask-Login to sign out user
    logout_user()

    # Prepare one-time system message
    flash(_('You have signed out successfully.'), 'success')

    # Redirect to logout_next endpoint or '/'
    next = request.args.get('next', _endpoint_url(user_manager.after_logout_endpoint))  # Get 'next' query param
    return redirect(next)


@login_required
def manage_emails():
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    user_emails = db_adapter.find_all_objects(db_adapter.UserEmailClass, user_id=int(current_user.get_id()))
    form = user_manager.add_email_form()

    # Process valid POST request
    if request.method=="POST" and form.validate():
        user_emails = db_adapter.add_object(db_adapter.UserEmailClass,
                user_id=int(current_user.get_id()),
                email=form.email.data)
        db_adapter.commit()
        return redirect(url_for('user.manage_emails'))

    # Process GET or invalid POST request
    return render_template(user_manager.manage_emails_template,
            user_emails=user_emails,
            form=form,
            )

def register():
    """ Display registration form and create new User."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    next = request.args.get('next', _endpoint_url(user_manager.after_login_endpoint))
    reg_next = request.args.get('reg_next', _endpoint_url(user_manager.after_register_endpoint))

    # Initialize form
    login_form = user_manager.login_form()                      # for login_or_register.html
    register_form = user_manager.register_form(request.form)    # for register.html
    if request.method!='POST':
        login_form.next.data    = register_form.next.data = next
        login_form.reg_next.data = register_form.reg_next.data = reg_next

    # Process valid POST
    if request.method=='POST' and register_form.validate():

        # Create a User object using Form fields that have a corresponding User field
        User = user_manager.db_adapter.UserClass
        user_class_fields = User.__dict__
        user_fields = {}

        # Create a UserEmail object using Form fields that have a corresponding UserEmail field
        if user_manager.db_adapter.UserEmailClass:
            UserEmail = user_manager.db_adapter.UserEmailClass
            user_email_class_fields = UserEmail.__dict__
            user_email_fields = {}

        # Create a UserProfile object using Form fields that have a corresponding UserProfile field
        if user_manager.db_adapter.UserProfileClass:
            UserProfile = user_manager.db_adapter.UserProfileClass
            user_profile_class_fields = UserProfile.__dict__
            user_profile_fields = {}

        # User.active is True if not USER_ENABLE_CONFIRM_EMAIL and False otherwise
        user_fields['active'] = not user_manager.enable_confirm_email

        # For all form fields
        for field_name, field_value in register_form.data.items():
            # Hash password field
            if field_name=='password':
                user_fields['password'] = user_manager.hash_password(register_form.password.data)
            # Store corresponding Form fields into the User object and/or UserProfile object
            else:
                if field_name in user_class_fields:
                    user_fields[field_name] = field_value
                if user_manager.db_adapter.UserEmailClass:
                    if field_name in user_email_class_fields:
                        user_email_fields[field_name] = field_value
                if user_manager.db_adapter.UserProfileClass:
                    if field_name in user_profile_class_fields:
                        user_profile_fields[field_name] = field_value

        # Add User record using named arguments 'user_fields'
        user = db_adapter.add_object(User, **user_fields)

        # Add UserEmail record using named arguments 'user_email_fields'
        if user_manager.db_adapter.UserEmailClass:
            user_email = db_adapter.add_object(UserEmail,
                    user=user,
                    is_primary=True,
                    **user_email_fields)
        else:
            user_email = None

        # Add UserProfile record using named arguments 'user_profile_fields'
        if user_manager.db_adapter.UserProfileClass:
            user.user_profile = db_adapter.add_object(UserProfile, **user_profile_fields)

        db_adapter.commit()

        # Send 'registered' email and delete new User object if send fails
        if user_manager.send_registered_email:
            try:
                # Send 'registered' email
                _send_registered_email(user, user_email)
            except Exception as e:
                # delete new User object if send  fails
                db_adapter.delete_object(user)
                db_adapter.commit()
                raise e

        # Send user_registered signal
        signals.user_registered.send(current_app._get_current_object(), user=user)

        # Redirect to login page or auto-login if configured
        reg_next = register_form.reg_next.data
        if user_manager.enable_confirm_email:
            return redirect(reg_next)
        if user_manager.auto_login_after_register:
            return _do_login_user(user, reg_next)  # Auto-login user after Register
        return redirect(_endpoint_url(user_manager.after_register_endpoint))

    # Process GET or invalid POST
    return render_template(user_manager.register_template,
            form=register_form,
            login_form=login_form,
            register_form=register_form)


def resend_confirm_email():
    """Prompt for email and re-send email conformation email."""
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Initialize form
    form = user_manager.resend_confirm_email_form(request.form)

    # Process valid POST
    if request.method=='POST' and form.validate():
        email = form.email.data

        # Find user by email
        user, user_email = user_manager.find_user_by_email(email)
        if user:
            _send_confirm_email(user, user_email)

        # Redirect to the login page
        return redirect(_endpoint_url(user_manager.after_resend_confirm_email_endpoint))

    # Process GET or invalid POST
    return render_template(user_manager.resend_confirm_email_template, form=form)


def reset_password(token):
    """ Verify the password reset token, Prompt for new password, and set the user's password."""
    # Verify token
    user_manager = current_app.user_manager
    db_adapter = user_manager.db_adapter

    is_valid, has_expired, user_id = user_manager.verify_token(
            token,
            user_manager.reset_password_expiration)

    if has_expired:
        flash(_('Your reset password token has expired.'), 'error')
        return redirect(url_for('user.login'))

    if not is_valid:
        flash(_('Your reset password token is invalid.'), 'error')
        return redirect(url_for('user.login'))

    user = user_manager.get_user_by_id(user_id)
    if user:
        # Avoid re-using old tokens
        if hasattr(user, 'reset_password_token'):
            verified = user.reset_password_token == token
        else:
            verified = True
    if not user or not verified:
        flash(_('Your reset password token is invalid.'), 'error')
        return redirect(_endpoint_url(user_manager.login_endpoint))

    # Initialize form
    form = user_manager.reset_password_form(request.form)

    # Process valid POST
    if request.method=='POST' and form.validate():
        # Invalidate the token by clearing the stored token
        if hasattr(user, 'reset_password_token'):
            db_adapter.update_object(user, reset_password_token='')

        # Change password
        hashed_password = user_manager.hash_password(form.new_password.data)
        db_adapter.update_object(user, password=hashed_password)
        db_adapter.commit()

        # Send 'password_changed' email
        if user_manager.enable_email and user_manager.send_password_changed_email:
            emails.send_password_changed_email(user)

        # Prepare one-time system message
        flash(_("Your password has been reset successfully. Please sign in with your new password"), 'success')

        # Redirect to the login page
        return redirect(url_for('user.login'))

    # Process GET or invalid POST
    return render_template(user_manager.reset_password_template, form=form)

def _get_email_address(user):
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter
    if db_adapter.UserEmailClass:
        user_email = db_adapter.find_first_object(db_adapter.UserEmailClass,
                user_id=int(user.get_id()),
                is_primary=True,
                )
        return user_email.email if user_email else None
    else:
        return user.email


def unauthenticated():
    """ Prepare a Flash message and redirect to USER_UNAUTHENTICATED_URL"""
    # Prepare Flash message
    url = request.url
    flash(_("You must be signed in to access '%(url)s'.", url=url), 'error')

    # quote the fully qualified url
    quoted_url = quote(url)

    # Redirect to USER_UNAUTHENTICATED_URL
    user_manager = current_app.user_manager
    return redirect(_endpoint_url(user_manager.unauthenticated_endpoint)+'?next='+ quoted_url)

def unauthorized():
    """ Prepare a Flash message and redirect to USER_UNAUTHORIZED_URL"""
    # Prepare Flash message
    url = request.script_root + request.path
    flash(_("You do not have permission to access '%(url)s'.", url=url), 'error')

    # Redirect to USER_UNAUTHORIZED_URL
    user_manager = current_app.user_manager
    return redirect(_endpoint_url(user_manager.unauthorized_endpoint))

def _send_registered_email(user, user_email):
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Send 'confirm_email' or 'registered' email
    if user_manager.enable_email and user_manager.enable_confirm_email:
        # Generate confirm email link
        object_id = user_email.id if user_email else int(user.get_id())
        token = user_manager.generate_token(object_id)
        confirm_email_link = url_for('user.confirm_email', token=token, _external=True)

        # Send email
        emails.send_registered_email(user, user_email, confirm_email_link)

        # Prepare one-time system message
        if user_manager.enable_confirm_email:
            email = user_email.email if user_email else user.email
            flash(_('A confirmation email has been sent to %(email)s with instructions to complete your registration.', email=email), 'success')
        else:
            flash(_('You have registered successfully.'), 'success')


def _send_confirm_email(user, user_email):
    user_manager =  current_app.user_manager
    db_adapter = user_manager.db_adapter

    # Send 'confirm_email' or 'registered' email
    if user_manager.enable_email and user_manager.enable_confirm_email:
        # Generate confirm email link
        object_id = user_email.id if user_email else int(user.get_id())
        token = user_manager.generate_token(object_id)
        confirm_email_link = url_for('user.confirm_email', token=token, _external=True)

        # Send email
        emails.send_confirm_email_email(user, user_email, confirm_email_link)

        # Prepare one-time system message
        email = user_email.email if user_email else user.email
        flash(_('A confirmation email has been sent to %(email)s with instructions to complete your registration.', email=email), 'success')


def _do_login_user(user, next, remember_me=False):
    if user and user.is_active:
        # Use Flask-Login to sign in user
        #print('login_user: remember_me=', remember_me)
        login_user(user, remember=remember_me)

        # Send user_logged_in signal
        signals.user_logged_in.send(current_app._get_current_object(), user=user)

        # Prepare one-time system message
        flash(_('You have signed in successfully.'), 'success')

        # Redirect to 'next' URL
        return redirect(next)

    return unauthenticated()

def _endpoint_url(endpoint):
    url = '/'
    if endpoint:
        url = url_for(endpoint)
    return url