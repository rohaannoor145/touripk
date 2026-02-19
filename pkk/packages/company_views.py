from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q
from django.core.exceptions import ValidationError
from functools import wraps
from .models import Company, Package, Booking, PackageReview
from content.models import Product, AdminNotification, Order, OrderItem
from users.security_utils import validate_file_upload, log_security_event
import logging
import re

logger = logging.getLogger(__name__)


def company_required(view_func):
    """Decorator to restrict views to company-type users only"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type != 'company':
            messages.error(request, 'Access denied. This area is for registered tour companies only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@company_required
def company_portal(request):
    """Company portal dashboard — only for company users"""
    company = Company.objects.filter(owner=request.user).first()

    if not company:
        messages.warning(request, 'No company found for your account. Please contact admin.')
        return render(request, 'packages/company_no_company.html')

    packages = Package.objects.filter(company=company).order_by('-created_at')
    products = Product.objects.filter(company=company).order_by('-created_at')

    company_bookings = Booking.objects.filter(
        package__company=company
    ).select_related('user', 'package').order_by('-created_at')[:10]

    # Recent product orders for this company's products
    company_product_ids = products.values_list('id', flat=True)
    recent_product_orders = Order.objects.filter(
        items__product__id__in=company_product_ids
    ).prefetch_related('items__product').select_related('user').order_by('-created_at').distinct()[:10]

    total_bookings = Booking.objects.filter(package__company=company).count()
    confirmed_bookings = Booking.objects.filter(
        package__company=company, status='confirmed'
    ).count()
    pending_bookings = Booking.objects.filter(
        package__company=company, status='pending'
    ).count()

    # Safely check if security questions are set up
    try:
        from users.models import SecurityAnswer
        has_security_answers = SecurityAnswer.objects.filter(user=request.user).exists()
    except Exception:
        has_security_answers = False

    context = {
        'company': company,
        'packages': packages,
        'products': products,
        'total_packages': packages.count(),
        'approved_packages': packages.filter(is_approved=True).count(),
        'total_products': products.count(),
        'approved_products': products.filter(is_approved=True).count(),
        'company_bookings': company_bookings,
        'recent_product_orders': recent_product_orders,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'has_security_answers': has_security_answers,
    }
    return render(request, 'packages/company_dashboard.html', context)


@company_required
def add_package(request):
    """Add new package — only for approved companies"""
    import re
    company = get_object_or_404(Company, owner=request.user)

    if company.approval_status != 'approved':
        messages.error(request, 'Your company must be approved first.')
        return redirect('packages:company_portal')

    context = {'company': company, 'package_types': Package.PACKAGE_TYPES}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        package_type = request.POST.get('package_type', '').strip()
        destination_names = request.POST.get('destination_names', '').strip()
        duration_days = request.POST.get('duration_days', '').strip()
        duration_nights = request.POST.get('duration_nights', '').strip()
        price_per_person = request.POST.get('price_per_person', '').strip()
        min_people = request.POST.get('min_people', '').strip()
        max_people = request.POST.get('max_people', '').strip()
        image = request.FILES.get('image')

        errors = []

        if not name:
            errors.append('Package name is required.')
        elif len(name) < 3:
            errors.append('Package name must be at least 3 characters.')
        elif len(name) > 200:
            errors.append('Package name cannot exceed 200 characters.')
        elif not re.search(r'[a-zA-Z]', name):
            errors.append('Package name must contain at least one letter.')

        valid_types = [t[0] for t in Package.PACKAGE_TYPES]
        if not package_type:
            errors.append('Package type is required.')
        elif package_type not in valid_types:
            errors.append('Invalid package type selected.')

        if not description:
            errors.append('Description is required.')
        elif len(description) < 20:
            errors.append('Description must be at least 20 characters.')

        if not destination_names:
            errors.append('At least one destination is required.')
        elif not re.search(r'[a-zA-Z]', destination_names):
            errors.append('Destinations must contain letters, not just numbers.')

        try:
            duration_days_int = int(duration_days)
            if duration_days_int < 1:
                errors.append('Days must be at least 1.')
            elif duration_days_int > 365:
                errors.append('Days cannot exceed 365.')
        except (ValueError, TypeError):
            errors.append('Days must be a valid whole number.')
            duration_days_int = None

        try:
            duration_nights_int = int(duration_nights)
            if duration_nights_int < 0:
                errors.append('Nights cannot be negative.')
            elif duration_nights_int > 365:
                errors.append('Nights cannot exceed 365.')
        except (ValueError, TypeError):
            errors.append('Nights must be a valid whole number.')
            duration_nights_int = None

        if duration_days_int and duration_nights_int is not None:
            if duration_nights_int > duration_days_int:
                errors.append('Nights cannot be more than Days.')

        try:
            price_val = float(price_per_person)
            if price_val <= 0:
                errors.append('Price must be greater than 0.')
            elif price_val > 99999999:
                errors.append('Price is unrealistically high.')
        except (ValueError, TypeError):
            errors.append('Price must be a valid number.')

        try:
            min_p = int(min_people) if min_people else 2
            if min_p < 1:
                errors.append('Min people must be at least 1.')
        except (ValueError, TypeError):
            errors.append('Min people must be a valid whole number.')
            min_p = 2

        try:
            max_p = int(max_people) if max_people else 10
            if max_p < 1:
                errors.append('Max people must be at least 1.')
        except (ValueError, TypeError):
            errors.append('Max people must be a valid whole number.')
            max_p = 10

        if min_p and max_p and max_p < min_p:
            errors.append('Max people cannot be less than Min people.')

        # Validate image upload
        if image:
            try:
                validate_file_upload(image, max_size_mb=5)
            except ValidationError as e:
                errors.append(str(e))

        if name:
            base_slug = slugify(name)
            if not base_slug:
                errors.append('Package name must produce a valid URL slug.')
            elif Package.objects.filter(slug=base_slug).exists():
                errors.append(f'Package name "{name}" already exists. Please use a different name.')

        if errors:
            for err in errors:
                messages.error(request, err)
            context['form_data'] = request.POST
            return render(request, 'packages/add_package.html', context)

        # Auto-approve if company is already approved
        auto_approve = company.approval_status == 'approved'
        Package.objects.create(
            company=company,
            name=name,
            slug=base_slug,
            description=description,
            package_type=package_type,
            destination_names=destination_names,
            duration_days=duration_days_int,
            duration_nights=duration_nights_int,
            price_per_person=price_val,
            inclusions='',
            min_people=min_p,
            max_people=max_p,
            image=image,
            is_active=True,
            is_approved=auto_approve
        )
        if auto_approve:
            messages.success(request, 'Package created and published successfully!')
        else:
            messages.success(request, 'Package created! Awaiting admin approval.')
        return redirect('packages:company_portal')

    return render(request, 'packages/add_package.html', context)


@company_required
def edit_package(request, package_id):
    """Edit existing package — only for company owner"""
    import re
    company = get_object_or_404(Company, owner=request.user)
    package = get_object_or_404(Package, id=package_id, company=company)

    context = {
        'company': company,
        'package': package,
        'package_types': Package.PACKAGE_TYPES,
    }

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        package_type = request.POST.get('package_type', '').strip()
        destination_names = request.POST.get('destination_names', '').strip()
        duration_days = request.POST.get('duration_days', '').strip()
        duration_nights = request.POST.get('duration_nights', '').strip()
        price_per_person = request.POST.get('price_per_person', '').strip()
        inclusions = request.POST.get('inclusions', '').strip()
        exclusions = request.POST.get('exclusions', '').strip()
        itinerary = request.POST.get('itinerary', '').strip()
        min_people = request.POST.get('min_people', '').strip()
        max_people = request.POST.get('max_people', '').strip()
        image = request.FILES.get('image')

        errors = []

        if not name:
            errors.append('Package name is required.')
        elif len(name) < 3:
            errors.append('Package name must be at least 3 characters.')
        elif not re.search(r'[a-zA-Z]', name):
            errors.append('Package name must contain at least one letter.')

        valid_types = [t[0] for t in Package.PACKAGE_TYPES]
        if package_type and package_type not in valid_types:
            errors.append('Invalid package type selected.')

        if not description or len(description) < 20:
            errors.append('Description must be at least 20 characters.')

        if not destination_names:
            errors.append('At least one destination is required.')

        try:
            duration_days_int = int(duration_days)
            if duration_days_int < 1:
                errors.append('Days must be at least 1.')
        except (ValueError, TypeError):
            errors.append('Days must be a valid whole number.')
            duration_days_int = package.duration_days

        try:
            duration_nights_int = int(duration_nights)
            if duration_nights_int < 0:
                errors.append('Nights cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Nights must be a valid whole number.')
            duration_nights_int = package.duration_nights

        try:
            price_val = float(price_per_person)
            if price_val <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Price must be a valid number.')
            price_val = float(package.price_per_person)

        try:
            min_p = int(min_people) if min_people else package.min_people
        except (ValueError, TypeError):
            min_p = package.min_people

        try:
            max_p = int(max_people) if max_people else package.max_people
        except (ValueError, TypeError):
            max_p = package.max_people

        if min_p and max_p and max_p < min_p:
            errors.append('Max people cannot be less than Min people.')

        # Validate image upload if provided
        if image:
            try:
                validate_file_upload(image, max_size_mb=5)
            except ValidationError as e:
                errors.append(str(e))

        # Check slug uniqueness if name changed
        new_slug = slugify(name)
        if new_slug != package.slug and Package.objects.filter(slug=new_slug).exclude(id=package.id).exists():
            errors.append(f'Package name "{name}" already exists.')

        if errors:
            for err in errors:
                messages.error(request, err)
            context['form_data'] = request.POST
            return render(request, 'packages/edit_package.html', context)

        package.name = name
        package.slug = new_slug
        package.description = description
        package.package_type = package_type
        package.destination_names = destination_names
        package.duration_days = duration_days_int
        package.duration_nights = duration_nights_int
        package.price_per_person = price_val
        package.inclusions = inclusions
        package.exclusions = exclusions
        package.itinerary = itinerary
        package.min_people = min_p
        package.max_people = max_p
        if image:
            package.image = image
        package.save()

        messages.success(request, 'Package updated successfully.')
        return redirect('packages:company_portal')

    return render(request, 'packages/edit_package.html', context)


@company_required
def delete_package(request, package_id):
    """Delete package — only for company owner, with booking protection"""
    company = get_object_or_404(Company, owner=request.user)
    package = get_object_or_404(Package, id=package_id, company=company)

    # Check for active bookings (pending or confirmed)
    active_bookings = Booking.objects.filter(
        package=package,
        status__in=['pending', 'confirmed']
    ).count()

    if request.method == 'POST':
        if active_bookings > 0:
            messages.error(
                request,
                f'Cannot delete "{package.name}" — it has {active_bookings} active booking(s). '
                f'Wait until all bookings are completed or cancelled.'
            )
            return redirect('packages:company_portal')

        package.delete()
        messages.success(request, 'Package deleted successfully.')
        return redirect('packages:company_portal')

    return render(request, 'packages/delete_package.html', {
        'package': package,
        'active_bookings': active_bookings,
    })


@company_required
def add_product(request):
    """Add new product — only for approved companies"""
    import re
    company = get_object_or_404(Company, owner=request.user)

    if company.approval_status != 'approved':
        messages.error(request, 'Your company must be approved first.')
        return redirect('packages:company_portal')

    categories = Product.CATEGORY_CHOICES
    context = {'company': company, 'categories': categories}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        category = request.POST.get('category', '').strip()
        stock_quantity = request.POST.get('stock_quantity', '0').strip()
        weight_kg = request.POST.get('weight_kg', '1.0').strip()
        image = request.FILES.get('image')

        errors = []

        if not name:
            errors.append('Product name is required.')
        elif len(name) < 3:
            errors.append('Product name must be at least 3 characters.')
        elif not re.search(r'[a-zA-Z]', name):
            errors.append('Product name must contain at least one letter.')

        if not description:
            errors.append('Description is required.')
        elif len(description) < 10:
            errors.append('Description must be at least 10 characters.')

        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Price must be a valid number.')
            price_val = 0

        valid_cats = [c[0] for c in Product.CATEGORY_CHOICES]
        if category and category not in valid_cats:
            errors.append('Invalid category selected.')

        try:
            stock_val = int(stock_quantity)
            if stock_val < 0:
                errors.append('Stock cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Stock must be a valid whole number.')
            stock_val = 0

        try:
            weight_val = float(weight_kg)
            if weight_val <= 0:
                errors.append('Weight must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Weight must be a valid number.')
            weight_val = 1.0

        # Validate image upload
        if image:
            try:
                validate_file_upload(image, max_size_mb=5)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            for err in errors:
                messages.error(request, err)
            context['form_data'] = request.POST
            return render(request, 'packages/add_product.html', context)

        product = Product.objects.create(
            name=name,
            description=description,
            price=price_val,
            category=category or 'handicrafts',
            stock_quantity=stock_val,
            weight_kg=weight_val,
            image=image,
            company=company,
            is_approved=company.approval_status == 'approved',
            is_active=True,
        )

        if company.approval_status != 'approved':
            # Notify admin only if company is not yet approved
            AdminNotification.objects.create(
                notification_type='general',
                title=f'New Product for Approval: {name}',
                message=f'{company.name} has added a new product "{name}" (PKR {price_val:,.0f}). Please review and approve.',
                link=f'/admin/content/product/{product.id}/change/',
            )
            messages.success(request, 'Product submitted for admin approval!')
        else:
            messages.success(request, 'Product added and published successfully!')
        return redirect('packages:company_portal')

    return render(request, 'packages/add_product.html', context)


@company_required
def edit_product(request, product_id):
    """Edit existing product — only for company owner"""
    import re
    company = get_object_or_404(Company, owner=request.user)
    product = get_object_or_404(Product, id=product_id, company=company)

    categories = Product.CATEGORY_CHOICES
    context = {'company': company, 'product': product, 'categories': categories}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        category = request.POST.get('category', '').strip()
        stock_quantity = request.POST.get('stock_quantity', '0').strip()
        weight_kg = request.POST.get('weight_kg', '1.0').strip()
        image = request.FILES.get('image')

        errors = []

        if not name or len(name) < 3:
            errors.append('Product name must be at least 3 characters.')
        if not description or len(description) < 10:
            errors.append('Description must be at least 10 characters.')

        try:
            price_val = float(price)
            if price_val <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Price must be a valid number.')
            price_val = float(product.price)

        try:
            stock_val = int(stock_quantity)
            if stock_val < 0:
                errors.append('Stock cannot be negative.')
        except (ValueError, TypeError):
            stock_val = product.stock_quantity

        try:
            weight_val = float(weight_kg)
            if weight_val <= 0:
                errors.append('Weight must be greater than 0.')
        except (ValueError, TypeError):
            weight_val = float(product.weight_kg)

        # Validate image upload if provided
        if image:
            try:
                validate_file_upload(image, max_size_mb=5)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            for err in errors:
                messages.error(request, err)
            context['form_data'] = request.POST
            return render(request, 'packages/edit_product.html', context)

        product.name = name
        product.description = description
        product.price = price_val
        product.category = category or product.category
        product.stock_quantity = stock_val
        product.weight_kg = weight_val
        if image:
            product.image = image
        product.save()

        messages.success(request, 'Product updated successfully.')
        return redirect('packages:company_portal')

    return render(request, 'packages/edit_product.html', context)


@company_required
def delete_product(request, product_id):
    """Delete product — only for company owner"""
    company = get_object_or_404(Company, owner=request.user)
    product = get_object_or_404(Product, id=product_id, company=company)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('packages:company_portal')

    return render(request, 'packages/delete_product.html', {'product': product})


@company_required
def company_bookings(request):
    """View all bookings for company's packages"""
    company = get_object_or_404(Company, owner=request.user)

    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(
        package__company=company
    ).select_related('user', 'package').order_by('-created_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'company': company,
        'bookings': bookings,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'packages/company_bookings.html', context)


@company_required
def update_booking_status(request, booking_id):
    """Update booking status — company can mark as completed"""
    company = get_object_or_404(Company, owner=request.user)
    booking = get_object_or_404(Booking, id=booking_id, package__company=company)

    if request.method == 'POST':
        new_status = request.POST.get('status', '')
        valid_statuses = [s[0] for s in Booking.STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking {booking.booking_reference} status updated to {booking.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('packages:company_bookings')
