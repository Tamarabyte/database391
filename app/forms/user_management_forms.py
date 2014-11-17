from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, HiddenField, SubmitField, ValidationError, validators
import re

from ..models import User, Person

class LoginForm(Form):
    
    username = StringField('Username', validators=[validators.Required('*required'),])
    password = PasswordField('Password', validators=[validators.Required('*required'),])
    submit = SubmitField('Sign in')
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):

        # Validate
        if not super(LoginForm, self).validate():
            return False

        # Find user by username
        user = User.query.get(self.username.data)
        
        # If the user doesn't exist throw an error
        if user is None:
            self.username.errors.append('*unknown username')
            return False
        
        # If the password doesn't match, throw an error
        if not user.verify_password(self.password.data):
            self.password.errors.append('*invalid password')
            return False
        
        # Save the user object in the form
        self.user = user
        return True
    

class RegistrationForm(Form):

    requiredValidator = validators.Required('*required')
    length24Validator = validators.Length(max=24, message='*max 24 characters')
    length128Validator = validators.Length(max=124, message='*max 128 characters')
    
    username = StringField('Username', validators=[requiredValidator, length24Validator])
    password = PasswordField('Password', validators=[requiredValidator, length24Validator])
    retype_password = PasswordField('Retype Password', validators=[requiredValidator, length24Validator, validators.EqualTo('password', message='*passwords did not match')])
    
    first_name = StringField('First Name', validators=[requiredValidator, length24Validator])
    last_name = StringField('Last Name', validators=[requiredValidator, length24Validator])
    address = StringField('Address', validators=[requiredValidator, length128Validator])
    email = StringField('Email', validators=[requiredValidator, length128Validator, validators.Email(message='*invalid email address.')])
    phone = StringField('Phone', validators=[requiredValidator])
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None
        self.person = None
        self.registration = None

    def validate(self):
        
        # Validate 
        if not super(RegistrationForm, self).validate():
            return False
        
        # Don't let users use any fun characters
        username = self.username.data
        if not re.match("^[\w\d_\-]*$", username):
            self.username.errors.append("*can only be letters, digits, '-' and '_'")
            return False
        
        # Username must unique
        user = User.query.get(username)
        if user is not None:
            self.username.errors.append('*already in use')
            return False
        
        # Name can't have any weird characters
        if not re.match("^[\w\d_\-']*$", self.first_name.data):
            self.first_name.errors.append("*invalid characters")
            return False
        
        if not re.match("^[\w\d_\-']*$", self.last_name.data):
            self.last_name.errors.append("*invalid characters")
            return False

        # Email must be unique
        person = Person.query.filter(Person.email == self.email.data).first()
        if person is not None:
            self.email.errors.append('*email is already in use')
            return False
        
        # Phone number must be 10 digits
        phone_number = ''.join([digit for digit in list(self.phone.data) if digit.isdigit()])

        if len(phone_number) != 10:
            self.phone.errors.append('*please use format XXX-XXX-XXXX {}'.format(phone_number))
            return False
        
        # Save objects in the form
        self.user = User(
            user_name=self.username.data,
            password=User.hash_password(self.password.data)
        )
        
        self.person = Person(
            user_name=self.username.data,
            first_name=self.first_name.data,
            last_name=self.last_name.data,
            address=self.address.data,
            email=self.email.data,
            phone=phone_number
        )
          
        return True
    
class ForgotPasswordForm(Form):
    
    requiredValidator = validators.Required('*required')
    
    email = StringField('Email', validators=[requiredValidator])
    
    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):

        # Validate
        if not super(ForgotPasswordForm, self).validate():
            return False

        # Find user by email
        user = User.query.join(Person).filter_by(email=self.email.data).first()

        # If the user doesn't exist throw an error
        if user is None:
            self.email.errors.append('*no account tied to ' + self.email.data)
            return False
        
        self.user = user
        self.person = Person.query.filter_by(email=self.email.data).first()
        
        return True
    
class ResetPasswordForm(Form):
    
    requiredValidator = validators.Required('*required')
    length24Validator = validators.Length(max=24, message='*max 24 characters')
    
    password = PasswordField('Password', validators=[requiredValidator, length24Validator])
    retype_password = PasswordField('Retype Password', validators=[requiredValidator, length24Validator, validators.EqualTo('password', message='*passwords did not match')])
    
    def validate(self):

        # Validate
        if not super(ResetPasswordForm, self).validate():
            return False

        return True
    