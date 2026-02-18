from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, SecurityAnswer
from .security_utils import validate_file_upload
import re


class UserRegistrationForm(UserCreationForm):
    """Secure user registration form with validation - Username, Email and Password"""
    
    username = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
            'autofocus': True
        }),
        help_text='Only English letters, digits, and @/./+/-/_ allowed. Must contain at least one letter.'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        }),
        help_text='We will send password reset links to this email'
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password',
            'autocomplete': 'new-password'
        }),
        help_text='Must be at least 8 characters with uppercase letters, lowercase letters and numbers'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password',
            'autocomplete': 'new-password'
        }),
        help_text='Enter the same password again for verification'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        """Validate username is unique and properly formatted"""
        username = self.cleaned_data.get('username', '').strip()
        
        if not username:
            raise ValidationError('Username is required')
        
        # Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken. Please choose a different one.')
        
        # Validate username pattern (ASCII English letters only, no unicode)
        if not re.match(r'^[a-zA-Z0-9.@+_-]+$', username):
            raise ValidationError('Username can only contain English letters, numbers, and @/./+/-/_ characters.')
        
        # Minimum length
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long')
        
        # Must contain at least one letter (reject all-numeric usernames like '1111222')
        if not re.search(r'[a-zA-Z]', username):
            raise ValidationError('Username must contain at least one letter. It cannot be all numbers.')
        
        return username
    
    def clean_email(self):
        """Validate email is unique and properly formatted"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError('Email is required')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered. Please login or use a different email.')
        
        # Validate email domain (basic check for common typos)
        domain = email.split('@')[-1]
        if domain.count('.') == 0:
            raise ValidationError('Please enter a valid email address with a proper domain')
        
        return email

    def clean_password1(self):
        """Additional password validation"""
        password = self.cleaned_data.get('password1')
        
        if not password:
            raise ValidationError('Password is required')
        
        # Minimum length
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase (capital) letter')
        
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number')
        
        # Check for common weak passwords
        common_passwords = ['12345678', 'password', 'password123', 'qwerty123', 'abc12345']
        if password.lower() in common_passwords:
            raise ValidationError('This password is too common. Please choose a stronger password.')
        
        return password

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        email = cleaned_data.get('email')
        
        # Check passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError('The two password fields must match')
        
        # Check password doesn't contain email
        if password1 and email:
            email_part = email.split('@')[0].lower()
            if email_part in password1.lower():
                self.add_error('password1', 'Password should not contain your email address')
        
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    """Secure login form with proper validation"""
    
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username',
            'autocomplete': 'username',
            'autofocus': True
        }),
        help_text='You can login with either your email or username'
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Remember me for 30 days'
    )
    
    error_messages = {
        'invalid_login': 'Invalid email or password. Please try again.',
        'inactive': 'This account has been disabled. Please contact support.',
    }

    def clean(self):
        """Additional login validation - Allow login with username or email"""
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username_or_email and password:
            # Check if input is an email
            if '@' in username_or_email:
                # It's an email - use directly
                username_or_email = username_or_email.lower()
                # Set it as the username for parent authentication
                self.cleaned_data['username'] = username_or_email
            else:
                # It's a username - find the email
                try:
                    user = CustomUser.objects.get(username=username_or_email)
                    # Replace with user's email since USERNAME_FIELD = 'email'
                    self.cleaned_data['username'] = user.email
                except CustomUser.DoesNotExist:
                    # User doesn't exist - will be caught by parent authentication
                    pass
        
        # Call parent clean to perform authentication
        # Parent expects email since USERNAME_FIELD = 'email'
        try:
            return super().clean()
        except ValidationError:
            # Re-raise with custom message
            raise ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
            )


class CompanyUserRegistrationForm(UserRegistrationForm):
    """Registration form for company/tour operator accounts"""

    company_name = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name',
        }),
        help_text='Must contain at least one letter. Min 3 characters.'
    )

    company_description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your tour company and services...',
        }),
        help_text='Minimum 20 characters.'
    )

    company_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'company@example.com',
        }),
        help_text='Official company email address.'
    )

    company_phone = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+92 300 1234567',
        }),
        help_text='9-15 digits. Example: +923001234567'
    )

    cnic_front = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        help_text='Upload a clear photo of the front side of your CNIC. Max 5MB.'
    )

    cnic_back = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        help_text='Upload a clear photo of the back side of your CNIC. Max 5MB.'
    )

    class Meta(UserRegistrationForm.Meta):
        model = CustomUser
        fields = ['password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove inherited fields; username is auto-generated from company_name
        if 'email' in self.fields:
            del self.fields['email']
        if 'username' in self.fields:
            del self.fields['username']

    def clean_cnic_front(self):
        """Validate CNIC front image with comprehensive security checks"""
        image = self.cleaned_data.get('cnic_front')
        if image:
            validate_file_upload(image, max_size_mb=5)
        return image

    def clean_cnic_back(self):
        """Validate CNIC back image with comprehensive security checks"""
        image = self.cleaned_data.get('cnic_back')
        if image:
            validate_file_upload(image, max_size_mb=5)
        return image

    def clean_company_name(self):
        """Validate company name"""
        name = self.cleaned_data.get('company_name', '').strip()
        if not name:
            raise ValidationError('Company name is required.')
        if len(name) < 3:
            raise ValidationError('Company name must be at least 3 characters long.')
        if not re.search(r'[a-zA-Z]', name):
            raise ValidationError('Company name must contain at least one letter.')
        if not re.match(r'^[a-zA-Z0-9\s&\-.]+$', name):
            raise ValidationError('Company name can only contain letters, numbers, spaces, &, hyphens, and periods.')
        return name

    def clean_company_description(self):
        """Validate company description"""
        desc = self.cleaned_data.get('company_description', '').strip()
        if not desc:
            raise ValidationError('Description is required.')
        if len(desc) < 20:
            raise ValidationError('Description must be at least 20 characters. Please provide more detail.')
        return desc

    def clean_company_phone(self):
        """Validate phone number"""
        phone = self.cleaned_data.get('company_phone', '').strip()
        if not phone:
            raise ValidationError('Phone number is required.')
        cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not re.match(r'^\+?\d{9,15}$', cleaned_phone):
            raise ValidationError('Please enter a valid phone number (9-15 digits).')
        return phone

    def save(self, commit=True):
        """Save user with company user type, auto-generating username from company name"""
        user = super().save(commit=False)
        user.user_type = 'company'
        # Auto-generate username from company name
        company_name = self.cleaned_data.get('company_name', '')
        base_username = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
        if not base_username:
            base_username = 'company'
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username
        if commit:
            user.save()
        return user


class ChangePasswordForm(forms.Form):
    """Form for changing password while logged in."""
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your current password'}),
    )
    new_password = forms.CharField(
        label='New Password',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )

    def clean_new_password(self):
        p = self.cleaned_data.get('new_password', '')
        import re as _re
        if len(p) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not _re.search(r'[A-Z]', p):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not _re.search(r'[a-z]', p):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not _re.search(r'\d', p):
            raise ValidationError('Password must contain at least one number.')
        return p

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password', '')
        p2 = cleaned.get('confirm_password', '')
        if p1 and p2 and p1 != p2:
            raise ValidationError('New passwords do not match.')
        return cleaned


class SecuritySetupForm(forms.Form):
    """Form for setting up the 3 security questions."""
    answer_1 = forms.CharField(
        label=SecurityAnswer.QUESTION_1,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your nickname'}),
    )
    answer_2 = forms.CharField(
        label=SecurityAnswer.QUESTION_2,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School name'}),
    )
    answer_3 = forms.CharField(
        label=SecurityAnswer.QUESTION_3,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City / place'}),
    )


class ForgotPasswordStep1Form(forms.Form):
    """Step 1: enter email to look up account."""
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'}),
    )


class ForgotPasswordStep2Form(forms.Form):
    """Step 2: answer the 3 security questions."""
    answer_1 = forms.CharField(
        label=SecurityAnswer.QUESTION_1,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your answer'}),
    )
    answer_2 = forms.CharField(
        label=SecurityAnswer.QUESTION_2,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your answer'}),
    )
    answer_3 = forms.CharField(
        label=SecurityAnswer.QUESTION_3,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your answer'}),
    )


class ForgotPasswordResetForm(forms.Form):
    """Step 3: set a new password."""
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password', '')
        p2 = cleaned.get('confirm_password', '')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Passwords do not match.')
        import re as _re
        if p1:
            if len(p1) < 8:
                raise ValidationError('Password must be at least 8 characters.')
            if not _re.search(r'[A-Z]', p1):
                raise ValidationError('Password must contain at least one uppercase letter.')
            if not _re.search(r'[a-z]', p1):
                raise ValidationError('Password must contain at least one lowercase letter.')
            if not _re.search(r'\d', p1):
                raise ValidationError('Password must contain at least one number.')
        return cleaned
