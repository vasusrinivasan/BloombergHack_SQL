""" Flask-User is a customizable user account management extension for Flask.

    :copyright: (c) 2013 by Ling Thio
    :author: Ling Thio (ling.thio@gmail.com)
    :license: Simplified BSD License, see LICENSE.txt for more details."""

from passlib.context import CryptContext
from flask import Blueprint, current_app
from flask_login import LoginManager, UserMixin as LoginUserMixin, make_secure_token
from flask_user.db_adapters import DBAdapter
from .db_adapters import SQLAlchemyAdapter
from . import emails
from . import forms
from . import passwords
from . import settings
from . import tokens
from . import translations
from . import views

# Enable the following: from flask.ext.user import current_user
from flask_login import current_user

# Enable the following: from flask.ext.user import login_required, roles_required
from .decorators import *

__version__ = '0.5.3'

def _flask_user_context_processor():
    """ Make 'user_manager' available to Jinja2 templates"""
    return dict(user_manager=current_app.user_manager)

class UserManager(object):
    """ This is the Flask-User object that manages the User management process."""

    def __init__(self, db_adapter, app=None,
                # Forms
                add_email_form=forms.AddEmailForm,
                change_password_form=forms.ChangePasswordForm,
                change_username_form=forms.ChangeUsernameForm,
                forgot_password_form=forms.ForgotPasswordForm,
                login_form=forms.LoginForm,
                register_form=forms.RegisterForm,
                resend_confirm_email_form=forms.ResendConfirmEmailForm,
                reset_password_form=forms.ResetPasswordForm,
                # Validators
                username_validator=forms.username_validator,
                password_validator=forms.password_validator,
                # View functions
                change_password_view_function=views.change_password,
                change_username_view_function=views.change_username,
                confirm_email_view_function=views.confirm_email,
                email_action_view_function=views.email_action,
                forgot_password_view_function=views.forgot_password,
                login_view_function=views.login,
                logout_view_function=views.logout,
                manage_emails_view_function=views.manage_emails,
                register_view_function=views.register,
                resend_confirm_email_view_function = views.resend_confirm_email,
                reset_password_view_function = views.reset_password,
                unauthenticated_view_function = views.unauthenticated,
                unauthorized_view_function = views.unauthorized,
                # Misc
                login_manager=LoginManager(),
                password_crypt_context=None,
                send_email_function = emails.send_email,
                token_manager=tokens.TokenManager(),
                ):
        """ Initialize the UserManager with custom or built-in attributes"""
        self.db_adapter = db_adapter
        # Forms
        self.add_email_form = add_email_form
        self.change_password_form = change_password_form
        self.change_username_form = change_username_form
        self.forgot_password_form = forgot_password_form
        self.login_form = login_form
        self.register_form = register_form
        self.resend_confirm_email_form = resend_confirm_email_form
        self.reset_password_form = reset_password_form
        # Validators
        self.username_validator = username_validator
        self.password_validator = password_validator
        # View functions
        self.change_password_view_function = change_password_view_function
        self.change_username_view_function = change_username_view_function
        self.confirm_email_view_function = confirm_email_view_function
        self.email_action_view_function = email_action_view_function
        self.forgot_password_view_function = forgot_password_view_function
        self.login_view_function = login_view_function
        self.logout_view_function = logout_view_function
        self.manage_emails_view_function = manage_emails_view_function
        self.register_view_function = register_view_function
        self.resend_confirm_email_view_function = resend_confirm_email_view_function
        self.reset_password_view_function = reset_password_view_function
        self.unauthenticated_view_function = unauthenticated_view_function
        self.unauthorized_view_function = unauthorized_view_function
        # Misc
        self.login_manager = login_manager
        self.token_manager = token_manager
        self.password_crypt_context = password_crypt_context
        self.send_email_function = send_email_function

        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """ Initialize app.user_manager."""
        # Bind Flask-USER to app
        app.user_manager = self
        # Flask seems to also support the current_app.extensions[] list
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['user'] = self

        # Set defaults for undefined settings
        settings.set_default_settings(self, app.config)

        # Make sure the settings are valid -- raise ConfigurationError if not
        settings.check_settings(self)

        # Initialize Translations -- Only if Flask-Babel has been installed
        if hasattr(app.jinja_env, 'install_gettext_callables'):
            app.jinja_env.install_gettext_callables(
                    translations.gettext,
                    translations.ngettext,
                    newstyle=True)

        # Create password_crypt_context if needed
        if not self.password_crypt_context:
            self.password_crypt_context = CryptContext(
                    schemes=[app.config['USER_PASSWORD_HASH']])

        # Setup Flask-Login
        self.setup_login_manager(app)

        # Setup TokenManager
        self.token_manager.setup(app.config.get('SECRET_KEY'))

        # Add flask_user/templates directory using a Blueprint
        blueprint = Blueprint('flask_user', 'flask_user', template_folder='templates')
        app.register_blueprint(blueprint)

        # Add URL routes
        self.add_url_routes(app)

        # Add context processor
        app.context_processor(_flask_user_context_processor)

        # Prepare for translations
        _ = translations.gettext


    def setup_login_manager(self, app):

        # Flask-Login calls this function to retrieve a User record by user ID.
        # Note: user_id is a UNICODE string returned by UserMixin.get_id().
        # See https://flask-login.readthedocs.org/en/latest/#how-it-works
        @self.login_manager.user_loader
        def load_user_by_id(user_unicode_id):
            user_id = int(user_unicode_id)
            #print('load_user_by_id: user_id=', user_id)
            return self.get_user_by_id(user_id)

        # Flask-login calls this function to retrieve a User record by user token.
        # A token is used to secure the user ID when stored in browser sessions.
        # See https://flask-login.readthedocs.org/en/latest/#alternative-tokens
        @self.login_manager.token_loader
        def load_user_by_token(token):
            user_id = self.token_manager.decrypt_id(token)
            #print('load_user_by_token: token=', token, 'user_id=', user_id)
            return self.get_user_by_id(int(user_id))

        self.login_manager.login_view = 'user.login'
        self.login_manager.init_app(app)


    def add_url_routes(self, app):
        """ Add URL Routes"""
        app.add_url_rule('/home',  'user.home',  self.login_view_function,  methods=['GET', 'POST'])
        app.add_url_rule(self.login_url,  'user.login',  self.login_view_function,  methods=['GET', 'POST'])
        app.add_url_rule(self.logout_url, 'user.logout', self.logout_view_function, methods=['GET', 'POST'])
        if self.enable_confirm_email:
            app.add_url_rule(self.confirm_email_url, 'user.confirm_email', self.confirm_email_view_function)
            app.add_url_rule(self.resend_confirm_email_url, 'user.resend_confirm_email', self.resend_confirm_email_view_function, methods=['GET', 'POST'])
        if self.enable_change_password:
            app.add_url_rule(self.change_password_url, 'user.change_password', self.change_password_view_function, methods=['GET', 'POST'])
        if self.enable_change_username:
            app.add_url_rule(self.change_username_url, 'user.change_username', self.change_username_view_function, methods=['GET', 'POST'])
        if self.enable_forgot_password:
            app.add_url_rule(self.forgot_password_url, 'user.forgot_password', self.forgot_password_view_function, methods=['GET', 'POST'])
            app.add_url_rule(self.reset_password_url, 'user.reset_password', self.reset_password_view_function, methods=['GET', 'POST'])
        if self.enable_register:
            app.add_url_rule(self.register_url, 'user.register', self.register_view_function, methods=['GET', 'POST'])
        if self.db_adapter.UserEmailClass:
            app.add_url_rule(self.email_action_url,  'user.email_action',  self.email_action_view_function)
            app.add_url_rule(self.manage_emails_url, 'user.manage_emails', self.manage_emails_view_function, methods=['GET', 'POST'])

    # Obsoleted function. Replace with hash_password()
    def generate_password_hash(self, password):
        return passwords.hash_password(self, password)

    def hash_password(self, password):
        return passwords.hash_password(self, password)

    def verify_password(self, password, hashed_password):
        return passwords.verify_password(self, password, hashed_password)

    def generate_token(self, user_id):
        return self.token_manager.generate_token(user_id)

    def verify_token(self, token, expiration_in_seconds):
        return self.token_manager.verify_token(token, expiration_in_seconds)

    def get_user_by_id(self, user_id):
        return self.db_adapter.get_object(self.db_adapter.UserClass, user_id)

    # NB: This backward compatibility function may be obsoleted in the future
    # Use 'get_user_by_id() instead.
    def find_user_by_id(self, user_id):
        return self.get_user_by_id(user_id)

    def get_user_email_by_id(self, user_email_id):
        return self.db_adapter.get_object(self.db_adapter.UserEmailClass, user_email_id)

    # NB: This backward compatibility function may be obsoleted in the future
    # Use 'get_user_email_by_id() instead.
    def find_user_email_by_id(self, user_email_id):
        return self.get_user_email_by_id(user_email_id)

    def find_user_by_username(self, username):
        return self.db_adapter.ifind_first_object(self.db_adapter.UserClass, username=username)

    def find_user_by_email(self, email):
        if self.db_adapter.UserEmailClass:
            user_email = self.db_adapter.ifind_first_object(self.db_adapter.UserEmailClass, email=email)
            user = user_email.user if user_email else None
        else:
            user_email = None
            user = self.db_adapter.ifind_first_object(self.db_adapter.UserClass, email=email)
        return (user, user_email)
    def find_user_by_phone(self, phone):
        user_phone = None
        user = self.db_adapter.ifind_first_object(self.db_adapter.UserClass, phone=phone)

    def email_is_available(self, new_email):
        """ Return True if new_email does not exist.
            Return False otherwise."""
        user, user_email = self.find_user_by_email(new_email)
        return (user==None)

    def username_is_available(self, new_username):
        """ Return True if new_username does not exist or if new_username equals old_username.
            Return False otherwise."""
        # Allow user to change username to the current username
        if current_user.is_authenticated() and new_username == current_user.username:
            return True
        # See if new_username is available
        return self.find_user_by_username(new_username)==None



class UserMixin(LoginUserMixin):
    """ This class adds methods to the User model class required by Flask-Login and Flask-User."""
    
    def has_roles(self, *requirements):
        """ Return True if the user has all of the specified roles. Return False otherwise.

            has_roles() accepts a list of requirements:
                has_role(requirement1, requirement2, requirement3).

            Each requirement is either a role_name, or a tuple_of_role_names.
                role_name example:   'manager'
                tuple_of_role_names: ('funny', 'witty', 'hilarious')
            A role_name-requirement is accepted when the user has this role.
            A tuple_of_role_names-requirement is accepted when the user has ONE of these roles.
            has_roles() returns true if ALL of the requirements have been accepted.

            For example:
                has_roles('a', ('b', 'c'), d)
            Translates to:
                User has role 'a' AND (role 'b' OR role 'c') AND role 'd'"""

        # Translates a list of role objects to a list of role_names
        user_roles = [role.name for role in self.roles]

        # has_role() accepts a list of requirements
        for requirement in requirements:
            if isinstance(requirement, (list, tuple)):
                # this is a tuple_of_role_names requirement
                tuple_of_role_names = requirement
                authorized = False
                for role_name in tuple_of_role_names:
                    if role_name in user_roles:
                        # tuple_of_role_names requirement was met: break out of loop
                        authorized = True
                        break
                if not authorized:
                    return False                    # tuple_of_role_names requirement failed: return False
            else:
                # this is a role_name requirement
                role_name = requirement
                # the user must have this role
                if not role_name in user_roles:
                    return False                    # role_name requirement failed: return False

        # All requirements have been met: return True
        return True

    # Flask-Login is capable of remembering the current user ID in the browser's session.
    # This function enables the user ID to be encrypted as a token.
    # See https://flask-login.readthedocs.org/en/latest/#remember-me
    def get_auth_token(self):
        token_manager = current_app.user_manager.token_manager
        user_id = int(self.get_id())
        token = token_manager.encrypt_id(user_id)
        #print('get_auth_token: user_id=', user_id, 'token=', token)
        return token
