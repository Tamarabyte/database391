"""
User Management Views seen by a user before logging in.
Include:
 - login view
 - registration view
 - lost password view
 - password change view

And contains helpers for sending registration emails,
and password reset emails
"""

import datetime
from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user
from flask_mail import Message
from app import app, db, mail
from ..forms.user_management_forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from ..models import User, Person

# Part of flask-login config
@app.login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@app.route('/', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def login():
    """ Login view. Takes the login form and validates username and password. Only lets registered users login. """

    form = LoginForm()

    if form.validate_on_submit():
        # Offer to resend the activation email if user who's registration is not confirmmed tries to login
        if form.user.date_registered is None:
            flash('Account not activated. <a href="/register/resend/{0}" class="alert-link">Resend your \
                  activation email?</a>'.format(form.username.data))
        else:
            login_user(form.user)
            return redirect('/home')

    return render_template('user_management/login.html', title='Sign In', form=form)

@app.route('/logout/', methods=['GET'])
def logout():
    """ Logout view. Ends user session. """
    logout_user()
    flash('You have signed out. Goodbye :(', 'success')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Displays form for user registration. On successful input sends registration confirmation email. """
    
    # Initialize form
    form = RegistrationForm()

    if form.validate_on_submit():

        try:
            send_registration_email(form.person)
            flash('A confirmation email has been sent to {} with instructions to complete your registration.'.format(form.person.email), 'success')
        except Exception as e:
            flash('Error sending the activation email. Please try again.')
            return redirect('/register')

        # Add the user and redirect to login
        db.session.add(form.user)
        db.session.commit()
        db.session.add(form.person)
        db.session.commit()
        return redirect('/login')

    # Process GET
    return render_template('user_management/registration.html', title="Sign Up", form=form)

@app.route('/login/<username>/<username_hash>/', methods=['GET'])
def login_registration_confirm(username, username_hash):
    """
    Confirms a user's registration and sets their registration date.
    When users register they recieve a url containing a hash of their username.
    This matches the hash in the URL to a hash of the user's name.
    Secure enough for our purposes.
    """

    user = User.query.get(username)
    if not user.validateActivationKey(username_hash):
        flash('The registration link you are trying to access is invalid.')
    elif user.date_registered is None:
        user.date_registered = datetime.date.today()
        db.session.commit()
        flash('Successfully registered! You may now sign in.', 'success')
    else:
        flash('This account is already active!')
    
    return redirect('/login')

@app.route('/register/resend/<username>/', methods=['GET'])
def resend_activation_email(username):
    """ Resends the activation email and redirects to login. """
    
    person = Person.query.get(username)
    try:
        send_registration_email(person)
        flash('A confirmation email has been sent to {} with instructions to complete your registration.'.format(person.email), 'success') 
    except Exception as e:
        flash('Error sending the activation email. Please try again.')
    return redirect('/login')

@app.route('/forgot/password', methods=['GET', 'POST'])
def forgot_password():
    """ Forgot password view displays a form for an email address. If
    The email address is linked to an account, a password reset email is sent to that account. """
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        try:
            send_password_reset_email(form.user, form.person)
            flash('An email has been sent to {} with instructions to reset your password.'.format(form.person.email), 'success')
        except Exception as e:
            flash('Error sending the password reset email. Please try again.')
        return redirect('/login')
    
    return render_template('user_management/forgot_password.html', title='Forgot Password', form=form)

@app.route('/reset/password/<username>/<password_hash>/', methods=['GET', 'POST'])
def reset_password(username, password_hash):
    """ Password reset email, uses a hash of the current users password in the url to confirm the user
    who is reseting their password. Secure enough for our purposes. """

    form = ResetPasswordForm()
    
    user = User.query.get(username)
    if not user.validatePasswordResetKey(password_hash):
        flash('The password reset link you are trying to access is invalid.')
        return redirect('/login')

    if form.validate_on_submit():
        user.password = User.hash_password(form.password.data)
        db.session.commit()
        flash('Your password has been successfully reset. You may now sign in.', 'success')
        return redirect('/login')
    
    return render_template('user_management/reset_password.html', title='Reset Password', form=form)

def send_password_reset_email(user, person):
    """ Builds and sends the password reset email. """
    
    # Generate confirm email link
    password_hash = User.createPasswordResetKey(user.password)
    link = url_for('reset_password', username=person.user_name, password_hash=password_hash, _external=True)

    # Send email
    message = Message(
        render_template('emails/password_reset_subject.txt'),
        sender='wildgamerappears@gmail.com',
        recipients =  [person.email]
        )
    message.body = render_template("emails/password_reset_message.txt", person=person, link=link)
    message.html = render_template("emails/password_reset_message.html", person=person, link=link)
        
    mail.send(message)
    
def send_registration_email(person):
    """ Builds and sends the registration email """
    
    # Generate confirm email link
    username_hash = User.createActivationKey(person.user_name)
    link = url_for('login_registration_confirm', username=person.user_name, username_hash=username_hash, _external=True)
    
    # Send email
    message = Message(
        render_template('emails/registration_subject.txt'),
        sender='wildgamerappears@gmail.com',
        recipients =  [person.email]
        )
    message.body = render_template("emails/registration_message.txt", person=person, link=link)
    message.html = render_template("emails/registration_message.html", person=person, link=link)
        
    mail.send(message)
