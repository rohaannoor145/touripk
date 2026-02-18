from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.conf import settings
from .models import Company, Package, Booking, PackageReview
from datetime import datetime
import stripe
import logging
import re as re_mod

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def package_list(request):
    """Display all packages grouped by company"""
    try:
        # Get filter parameters
        company_slug = request.GET.get('company')
        package_type = request.GET.get('type')
        search_query = request.GET.get('search', '').strip()
        
        # Start with active AND approved packages only
        packages = Package.objects.filter(is_active=True, is_approved=True).select_related('company')
        
        # Apply search filter
        if search_query:
            packages = packages.filter(
                Q(name__icontains=search_query) |
                Q(destination_names__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(company__name__icontains=search_query)
            )
        
        # Apply filters
        if company_slug:
            packages = packages.filter(company__slug=company_slug)
        if package_type:
            packages = packages.filter(package_type=package_type)
        
        # Get all active companies that have active packages
        companies = Company.objects.filter(
            is_active=True,
            approval_status='approved',
            packages__is_active=True
        ).annotate(
            active_package_count=Count('packages', filter=Q(packages__is_active=True))
        ).filter(active_package_count__gt=0).distinct()
        
        # Pagination
        paginator = Paginator(packages, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'packages': page_obj.object_list,
            'companies': companies,
            'selected_company': company_slug,
            'selected_type': package_type,
            'search_query': search_query,
            'package_types': Package.PACKAGE_TYPES,
        }
        
        return render(request, 'packages/package_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in package_list view: {str(e)}")
        return render(request, 'packages/package_list.html', {
            'packages': [],
            'companies': [],
            'error': 'Unable to load packages at this time.'
        })


def package_detail(request, slug):
    """Display detailed package information"""
    from django.http import Http404
    try:
        package = get_object_or_404(Package, slug=slug, is_active=True)
        
        # Increment view count
        package.views_count += 1
        package.save(update_fields=['views_count'])
        
        # Get related packages from the same company
        related_packages = Package.objects.filter(
            company=package.company,
            is_active=True
        ).exclude(id=package.id)[:3]
        
        # Get reviews for this package
        reviews = PackageReview.objects.filter(package=package).select_related('user').order_by('-created_at')
        
        context = {
            'package': package,
            'related_packages': related_packages,
            'reviews': reviews,
        }
        
        return render(request, 'packages/package_detail.html', context)
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Error in package_detail view: {str(e)}", exc_info=True)
        return render(request, 'packages/package_detail.html', {
            'error': 'Package not found.'
        })


def company_detail(request, slug):
    """Display company information and their packages"""
    try:
        company = get_object_or_404(Company, slug=slug, is_active=True)
        packages = Package.objects.filter(company=company, is_active=True)
        
        # Pagination
        paginator = Paginator(packages, 9)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'company': company,
            'page_obj': page_obj,
            'packages': page_obj.object_list,
        }
        
        return render(request, 'packages/company_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in company_detail view: {str(e)}")
        return render(request, 'packages/company_detail.html', {
            'error': 'Company not found.'
        })


@login_required
def create_booking(request, package_id):
    """Handle booking creation"""
    if request.method == 'POST':
        try:
            package = get_object_or_404(Package, id=package_id, is_active=True)
            
            # Extract form data
            travel_date_str = request.POST.get('travel_date')
            num_adults = int(request.POST.get('num_adults', 1))
            num_children = int(request.POST.get('num_children', 0))
            phone = request.POST.get('phone')
            special_requests = request.POST.get('special_requests', '')
            
            # Validate travel date
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            
            # Calculate total amount
            adult_price = package.price_per_person * num_adults
            child_price = (package.child_price or package.price_per_person) * num_children
            total_amount = adult_price + child_price
            
            # Create booking in database
            booking = Booking.objects.create(
                user=request.user,
                package=package,
                travel_date=travel_date,
                num_adults=num_adults,
                num_children=num_children,
                phone=phone,
                special_requests=special_requests,
                total_amount=total_amount,
                status='pending'
            )
            
            # Store booking ID in session for payment page
            request.session['pending_booking_id'] = booking.id
            
            # Redirect to payment page
            return redirect('packages:payment_page', booking_id=booking.id)
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            messages.error(request, 'Unable to process your booking. Please try again or contact support.')
            return redirect('packages:package_detail', slug=package.slug)
    
    return redirect('packages:package_list')


def booking_confirmation(request):
    """Display booking confirmation"""
    booking_id = request.session.get('last_booking_id')
    
    if not booking_id:
        messages.warning(request, 'No booking information found.')
        return redirect('packages:package_list')
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        context = {'booking': booking}
        return render(request, 'packages/booking_confirmation.html', context)
    except Exception as e:
        logger.error(f'Error retrieving booking confirmation (ID:{booking_id}): {str(e)}')
        messages.error(request, 'Unable to retrieve booking information.')
        return redirect('packages:package_list')


@login_required
def payment_page(request, booking_id):
    """Display payment page for booking"""
    try:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        
        # Check if already paid
        if booking.status == 'confirmed':
            request.session['last_booking_id'] = booking.id
            messages.info(request, 'This booking has already been paid.')
            return redirect('packages:booking_confirmation')
        
        context = {
            'booking': booking,
            'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        }
        return render(request, 'packages/payment_page.html', context)
    except Exception as e:
        logger.error(f'Error loading payment page (Booking ID:{booking_id}): {str(e)}')
        messages.error(request, 'Booking not found.')
        return redirect('packages:package_list')


@login_required
def create_booking_payment_intent(request, booking_id):
    """Create Stripe PaymentIntent for a booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status == 'confirmed':
        return JsonResponse({'error': 'Already paid'}, status=400)

    try:
        amount_in_paisa = int(booking.total_amount * 100)
        test_amount = max(50, min(amount_in_paisa, 99999999))

        intent = stripe.PaymentIntent.create(
            amount=test_amount,
            currency='usd',
            metadata={
                'booking_id': booking.id,
                'booking_reference': booking.booking_reference,
                'user_id': request.user.id,
                'package': booking.package.name,
                'actual_amount_pkr': str(booking.total_amount),
            },
            description=f'Booking #{booking.booking_reference} - {booking.package.name}',
        )

        booking.stripe_payment_intent_id = intent.id
        booking.payment_method = 'stripe'
        booking.save()

        return JsonResponse({'clientSecret': intent.client_secret})
    except Exception as e:
        logger.error(f"Stripe PaymentIntent creation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def booking_payment_success(request, booking_id):
    """Handle successful Stripe payment for a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status != 'confirmed':
        booking.status = 'confirmed'
        booking.payment_method = 'stripe'
        booking.save()

    request.session['last_booking_id'] = booking.id
    messages.success(
        request,
        f'Payment successful! Your booking is confirmed. Booking Reference: {booking.booking_reference}'
    )
    return redirect('packages:booking_confirmation')


@login_required
def process_payment(request, booking_id):
    """Process bank transfer payment"""
    if request.method == 'POST':
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)

            payment_method = request.POST.get('payment_method')
            transaction_id = request.POST.get('transaction_id', '').strip()

            if payment_method == 'bank':
                if not transaction_id:
                    messages.error(request, 'Please enter the Transaction ID/Reference from your bank receipt.')
                    return redirect('packages:payment_page', booking_id=booking_id)
                if not re_mod.match(r'^[A-Za-z0-9\-]{5,50}$', transaction_id):
                    messages.error(request, 'Transaction ID must be 5-50 characters (letters, numbers, hyphens only).')
                    return redirect('packages:payment_page', booking_id=booking_id)

                booking.status = 'confirmed'
                booking.payment_method = 'bank'
                booking.transaction_id = transaction_id
                booking.save()

                request.session['last_booking_id'] = booking.id
                messages.success(
                    request,
                    f'Payment successful! Your booking is confirmed. Booking Reference: {booking.booking_reference}'
                )
                return redirect('packages:booking_confirmation')

            messages.error(request, 'Invalid payment method.')
            return redirect('packages:payment_page', booking_id=booking_id)

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            messages.error(request, 'Payment processing failed. Please try again.')
            return redirect('packages:payment_page', booking_id=booking_id)

    return redirect('packages:package_list')


@login_required
def add_package_review(request, slug, booking_id):
    """Add a review for a package after completed booking"""
    package = get_object_or_404(Package, slug=slug)
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, package=package)

    # Only allow review for completed bookings
    if booking.status != 'completed':
        messages.error(request, 'You can only review a package after completing the tour.')
        return redirect('packages:my_bookings')

    # Check if already reviewed
    if PackageReview.objects.filter(user=request.user, package=package).exists():
        messages.info(request, 'You have already reviewed this package.')
        return redirect('packages:package_detail', slug=slug)

    if request.method == 'POST':
        rating = request.POST.get('rating', '')
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        errors = []
        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                errors.append('Rating must be between 1 and 5.')
        except (ValueError, TypeError):
            errors.append('Please select a valid rating.')
            rating_val = 0

        if not title or len(title) < 3:
            errors.append('Review title must be at least 3 characters.')
        if not comment or len(comment) < 10:
            errors.append('Review comment must be at least 10 characters.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'packages/add_review.html', {
                'package': package,
                'booking': booking,
                'form_data': request.POST,
            })

        PackageReview.objects.create(
            user=request.user,
            package=package,
            booking=booking,
            rating=rating_val,
            title=title,
            comment=comment,
        )

        # Update package average rating
        avg = package.get_average_rating()
        package.rating = avg
        package.save(update_fields=['rating'])

        messages.success(request, 'Thank you for your review!')
        return redirect('packages:package_detail', slug=slug)

    return render(request, 'packages/add_review.html', {
        'package': package,
        'booking': booking,
    })


@login_required
def my_bookings(request):
    """View user's package bookings"""
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('package', 'package__company').order_by('-created_at')

    # Check which bookings already have reviews
    reviewed_booking_ids = set(
        PackageReview.objects.filter(user=request.user).values_list('booking_id', flat=True)
    )

    context = {
        'bookings': bookings,
        'reviewed_booking_ids': reviewed_booking_ids,
    }
    return render(request, 'packages/my_bookings.html', context)
