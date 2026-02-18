from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import CreateView, FormView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django_ratelimit.decorators import ratelimit
from .models import CustomUser, SecurityAnswer
from .forms import (UserRegistrationForm, UserLoginForm, CompanyUserRegistrationForm,
                    SecuritySetupForm, ForgotPasswordStep1Form,
                    ForgotPasswordStep2Form, ForgotPasswordResetForm)
from content.models import Destination, Product
from packages.models import Company, Booking
from .security_utils import log_security_event, validate_file_upload
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class UserRegisterView(CreateView):
    """Secure user registration with proper validation"""
    model = CustomUser
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

    @method_decorator(sensitive_post_parameters('password1', 'password2'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(ratelimit(key='ip', rate='15/h', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Save user with hashed password and log the registration"""
        try:
            user = form.save(commit=False)
            user.email = user.email.lower()  # Normalize email
            # Username is now provided by the user in the form
            # Set full_name from username
            user.full_name = user.username
            user.user_type = 'user'  # Explicitly set as regular user
            user.save()
            
            logger.info(f"New user registered: {user.username} ({user.email})")
            
            messages.success(
                self.request,
                'Registration successful! Your account has been created. Please login to continue.'
            )
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(self.request, f'Registration failed: {str(e)}. Please contact support if this persists.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission - errors are shown in the form itself"""
        logger.warning(f"Invalid registration attempt: {form.errors}")
        # Don't add generic message - detailed errors are shown in template
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Your Account'
        return context


class CompanyRegisterView(CreateView):
    """Registration view for company/tour operator accounts"""
    model = CustomUser
    form_class = CompanyUserRegistrationForm
    template_name = 'users/company_register.html'
    success_url = reverse_lazy('login')

    @method_decorator(sensitive_post_parameters('password1', 'password2'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        """Include request.FILES for image uploads"""
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs['files'] = self.request.FILES
        return kwargs

    def form_valid(self, form):
        """Create user account AND company object together"""
        try:
            # Save user with company type
            user = form.save(commit=False)
            user.email = form.cleaned_data['company_email'].lower()
            user.full_name = form.cleaned_data['company_name']
            user.user_type = 'company'
            user.save()

            # Create the Company object
            company_name = form.cleaned_data['company_name']
            base_slug = slugify(company_name)

            # Handle slug collision
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            Company.objects.create(
                owner=user,
                name=company_name,
                slug=slug,
                description=form.cleaned_data['company_description'],
                email=form.cleaned_data['company_email'],
                phone=form.cleaned_data['company_phone'],
                cnic_front=form.cleaned_data.get('cnic_front'),
                cnic_back=form.cleaned_data.get('cnic_back'),
                approval_status='pending',
            )

            # Log company registration
            log_security_event(
                'company_registration',
                user,
                {
                    'company_name': company_name,
                    'email': form.cleaned_data['company_email'],
                    'ip': self.request.META.get('REMOTE_ADDR')
                },
                level='info'
            )

            messages.success(
                self.request,
                'Registration successful! Your approval request has been sent to admin. '
                'You will receive a notification once your company is approved. Please login to continue.'
            )
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Company registration error: {str(e)}")
            messages.error(self.request, f'Company registration failed: {str(e)}. Please contact support if this persists.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission - errors are shown in the form itself"""
        logger.warning(f"Invalid company registration attempt: {form.errors}")
        # Don't add generic message - detailed errors are shown in template
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Register Your Company'
        return context


class UserLoginView(FormView):
    """Secure login view with rate limiting and session management"""
    form_class = UserLoginForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('dashboard')

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(ratelimit(key='ip', rate='10/5m', method='POST', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        """Authenticate and login user with session management"""
        try:
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Authenticate user
            user = authenticate(self.request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(self.request, user)
                    
                    # Set session expiry based on remember_me
                    if remember_me:
                        self.request.session.set_expiry(2592000)  # 30 days
                    else:
                        self.request.session.set_expiry(0)  # Browser close
                    
                    # Log successful login
                    log_security_event(
                        'successful_login',
                        user,
                        {
                            'ip': self.request.META.get('REMOTE_ADDR'),
                            'user_agent': self.request.META.get('HTTP_USER_AGENT', '')[:100],
                            'remember_me': remember_me
                        },
                        level='info'
                    )
                    
                    # Check if company user and approval status
                    if user.user_type == 'company':
                        try:
                            from packages.models import Company
                            company = Company.objects.filter(owner=user).first()
                            if company and company.approval_status == 'pending':
                                messages.warning(
                                    self.request, 
                                    'Your company registration is pending admin approval. '
                                    'You will be able to access the company portal once your company is approved.'
                                )
                                # Logout the user since they can't access company features yet
                                from django.contrib.auth import logout
                                logout(self.request)
                                return redirect('login')
                            elif company and company.approval_status == 'rejected':
                                messages.error(
                                    self.request,
                                    f'Your company registration was rejected. Reason: {company.rejection_reason or "Please contact admin for details."}'
                                )
                                from django.contrib.auth import logout
                                logout(self.request)
                                return redirect('login')
                        except Exception as e:
                            logger.error(f"Company status check error: {str(e)}")
                    
                    messages.success(self.request, f'Welcome, {user.full_name}!')
                    
                    # Redirect based on user type
                    next_url = self.request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    elif user.user_type == 'company':
                        return redirect('packages:company_portal')
                    else:
                        return redirect(self.success_url)
                else:
                    # Log disabled account login attempt
                    log_security_event(
                        'disabled_account_login',
                        username,
                        {'ip': self.request.META.get('REMOTE_ADDR')},
                        level='warning'
                    )
                    messages.error(self.request, 'Your account has been disabled.')
            else:
                # Log failed login attempt
                log_security_event(
                    'failed_login',
                    username,
                    {'ip': self.request.META.get('REMOTE_ADDR')},
                    level='warning'
                )
                messages.error(self.request, 'Invalid email or password.')
            
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            messages.error(self.request, f'Login error: {str(e)}. Please contact support if this persists.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid login - errors are shown in the form itself"""
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login to Your Account'
        return context


@login_required
def dashboard(request):
    """User dashboard — redirects company users to company portal"""
    # Redirect company users to their portal
    if request.user.user_type == 'company':
        return redirect('packages:company_portal')

    try:
        destinations = Destination.objects.all()
        products = Product.objects.all()
        
        # Get user's recent bookings with related data
        recent_bookings = Booking.objects.filter(
            user=request.user
        ).select_related(
            'package', 'package__company'
        ).order_by('-created_at')[:5]
        
        # Get booking statistics
        total_bookings = Booking.objects.filter(user=request.user).count()
        confirmed_bookings = Booking.objects.filter(
            user=request.user, status='confirmed'
        ).count()
        pending_bookings = Booking.objects.filter(
            user=request.user, status='pending'
        ).count()
        
        return render(request, 'users/dashboard.html', {
            'destinations': destinations,
            'products': products,
            'recent_bookings': recent_bookings,
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'pending_bookings': pending_bookings,
        })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        messages.error(request, 'Error loading dashboard data.')
        return render(request, 'users/dashboard.html', {})


def logout_view(request):
    """Custom logout view with better error handling"""
    from django.contrib.auth import logout
    from django.views.decorators.csrf import csrf_protect
    from django.views.decorators.http import require_http_methods
    
    if request.method == 'POST':
        try:
            # Log logout before it happens
            if request.user.is_authenticated:
                log_security_event(
                    'logout',
                    request.user,
                    {'ip': request.META.get('REMOTE_ADDR')},
                    level='info'
                )
            
            logout(request)
            messages.success(request, 'You have been successfully logged out.')
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            messages.warning(request, 'Logged out (with minor issues).')
        return redirect('home')
    else:
        # If GET request, show message and redirect
        messages.info(request, 'Please use the logout button to sign out.')
        return redirect('home')


# ─── Security Questions ──────────────────────────────────────────────────────

@login_required
def setup_security_questions(request):
    """Allow a logged-in user to set / update their 3 security answers."""
    try:
        obj = request.user.security_answers
    except SecurityAnswer.DoesNotExist:
        obj = None

    if request.method == 'POST':
        form = SecuritySetupForm(request.POST)
        if form.is_valid():
            if obj is None:
                obj = SecurityAnswer(user=request.user)
            obj.set_answers(
                form.cleaned_data['answer_1'],
                form.cleaned_data['answer_2'],
                form.cleaned_data['answer_3'],
            )
            obj.save()
            messages.success(request, 'Security questions saved successfully!')
            return redirect('dashboard')
    else:
        form = SecuritySetupForm()

    return render(request, 'users/security_setup.html', {
        'form': form,
        'already_set': obj is not None,
    })


def forgot_password_step1(request):
    """Step 1 – enter email address."""
    if request.method == 'POST':
        form = ForgotPasswordStep1Form(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            try:
                user = CustomUser.objects.get(email=email)
                # Check if security questions are set up
                if not hasattr(user, 'security_answers'):
                    messages.error(request, 'No security questions found for this account. Please contact support.')
                    return render(request, 'users/forgot_step1.html', {'form': form})
                # Store user id in session for next step (not token-based, just session)
                request.session['pwd_reset_uid'] = user.pk
                return redirect('forgot_password_step2')
            except CustomUser.DoesNotExist:
                # Don't reveal whether email exists
                messages.error(request, 'No account found with that email address.')
    else:
        form = ForgotPasswordStep1Form()

    return render(request, 'users/forgot_step1.html', {'form': form})


def forgot_password_step2(request):
    """Step 2 – answer the 3 security questions."""
    uid = request.session.get('pwd_reset_uid')
    if not uid:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password_step1')

    try:
        user = CustomUser.objects.get(pk=uid)
        sec = user.security_answers
    except (CustomUser.DoesNotExist, SecurityAnswer.DoesNotExist):
        messages.error(request, 'Invalid session. Please start again.')
        return redirect('forgot_password_step1')

    if request.method == 'POST':
        form = ForgotPasswordStep2Form(request.POST)
        if form.is_valid():
            if sec.check_answers(
                form.cleaned_data['answer_1'],
                form.cleaned_data['answer_2'],
                form.cleaned_data['answer_3'],
            ):
                request.session['pwd_reset_verified'] = True
                return redirect('forgot_password_reset')
            else:
                messages.error(request, 'One or more answers are incorrect. Please try again.')
    else:
        form = ForgotPasswordStep2Form()

    return render(request, 'users/forgot_step2.html', {'form': form})


def forgot_password_reset(request):
    """Step 3 – set a new password after verification."""
    uid = request.session.get('pwd_reset_uid')
    verified = request.session.get('pwd_reset_verified')

    if not uid or not verified:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password_step1')

    try:
        user = CustomUser.objects.get(pk=uid)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid session.')
        return redirect('forgot_password_step1')

    if request.method == 'POST':
        form = ForgotPasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            # Clear session keys
            request.session.pop('pwd_reset_uid', None)
            request.session.pop('pwd_reset_verified', None)
            messages.success(request, 'Password reset successful! You can now log in with your new password.')
            return redirect('login')
    else:
        form = ForgotPasswordResetForm()

    return render(request, 'users/forgot_reset.html', {'form': form})
