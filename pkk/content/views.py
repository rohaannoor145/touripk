from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import F
from decimal import Decimal
from .models import Destination, Product, CostComponent, Cart, CartItem, Order, OrderItem, CustomPackageOrder, AdminNotification, ProductReview
from packages.models import Company, Package
from .utils.weather import get_weather_data
from django.conf import settings
from django.utils import timezone
from users.security_utils import log_security_event
import stripe
import json
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    featured_destinations = Destination.objects.filter(is_featured=True, is_active=True)[:6]
    companies = Company.objects.filter(is_active=True, approval_status='approved').order_by('name')
    products = Product.objects.filter(is_active=True).order_by('-is_featured', 'name')
    featured_packages = Package.objects.filter(
        is_active=True, is_approved=True, is_featured=True
    ).select_related('company').order_by('-created_at')[:6]
    all_packages = Package.objects.filter(
        is_active=True, is_approved=True
    ).select_related('company').order_by('-created_at')[:8]
    return render(request, 'content/home.html', {
        'featured_destinations': featured_destinations,
        'companies': companies,
        'products': products,
        'featured_packages': featured_packages,
        'all_packages': all_packages,
    })

def destination_list(request):
    # Get search parameter
    search_query = request.GET.get('search', '').strip()
    
    # Start with active destinations
    destinations = Destination.objects.filter(is_active=True).order_by('-is_featured', 'name')
    
    # Apply search filter if provided
    if search_query:
        from django.db.models import Q
        destinations = destinations.filter(
            Q(name__icontains=search_query) | 
            Q(city__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    return render(request, 'content/destination_list.html', {
        'destinations': destinations,
        'search_query': search_query
    })

def destination_detail(request, pk):
    destination = get_object_or_404(Destination, pk=pk, is_active=True)
    return render(request, 'content/destination_detail.html', {'destination': destination})

def product_list(request):
    # Get filter parameters
    category = request.GET.get('category', '')
    search_query = request.GET.get('search', '').strip()
    
    # Start with active AND approved products
    products = Product.objects.filter(is_active=True, is_approved=True).order_by('-is_featured', 'name')
    
    # Apply category filter
    if category:
        products = products.filter(category=category)
    
    # Apply search filter
    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)
    
    # Get all categories for filter dropdown
    categories = Product.CATEGORY_CHOICES if hasattr(Product, 'CATEGORY_CHOICES') else [
        ('clothing', 'Clothing'),
        ('food', 'Food & Beverages'),
        ('handicrafts', 'Handicrafts'),
        ('books', 'Books & Media'),
        ('accessories', 'Accessories'),
    ]
    
    return render(request, 'content/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category,
        'search_query': search_query,
    })

@login_required
def cost_calculator(request):
    from datetime import date
    destinations = Destination.objects.filter(is_active=True).order_by('name')
    return render(request, 'content/cost_calculator.html', {
        'destinations': destinations,
        'today': date.today().isoformat()
    })

def get_destination_costs(request):
    try:
        destination_id = request.GET.get('destination_id')
        if destination_id:
            cost_components = CostComponent.objects.filter(destination_id=destination_id)
            data = [{
                'id': comp.id,
                'name': comp.name,
                'category': comp.category,
                'base_cost': float(comp.base_cost),
                'unit': comp.unit,
                'description': comp.description
            } for comp in cost_components]
            return JsonResponse({'costs': data})
        return JsonResponse({'costs': []})
    except Exception as e:
        logger.error(f"Error fetching destination costs: {str(e)}")
        return JsonResponse({'error': 'Failed to fetch costs'}, status=500)

@login_required
def check_weather(request):
    weather_data = None
    city = request.GET.get('city')
    
    if city:
        try:
            weather_data = get_weather_data(city)
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            weather_data = None
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'weather_data': weather_data})
    
    return render(request, 'content/check_weather.html', {
        'weather_data': weather_data,
        'city': city
    })

def tour_calculator_advanced(request):
    """Advanced tour calculator with detailed cost breakdown"""
    from datetime import date
    return render(request, 'content/tour_calculator_advanced.html', {
        'today': date.today().isoformat()
    })

def tour_packages(request):
    """Tour packages listing page"""
    return render(request, 'content/tour_packages.html')

def custom_package(request):
    """Custom package creation page"""
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to create a custom package.')
            return redirect('login')
        
        destination = request.POST.get('destination', '')
        num_days = int(request.POST.get('numDays', 3))
        num_people = int(request.POST.get('numPeople', 7))
        num_rooms = int(request.POST.get('numRooms', 2))
        vehicle = request.POST.get('vehicle', 'grand-cabin')
        food = request.POST.get('food', 'none')
        accommodation = request.POST.get('accommodation', 'standard')
        guide = request.POST.get('guide', 'no') == 'yes'
        bonfire = request.POST.get('bonfire', 'no') == 'yes'
        total_price = Decimal(request.POST.get('totalPrice', '0').replace(',', ''))
        per_person_price = Decimal(request.POST.get('perPersonPrice', '0').replace(',', ''))
        
        # Clamp values
        num_days = max(3, min(10, num_days))
        num_people = max(7, min(27, num_people))
        
        # Create CustomPackageOrder
        order = CustomPackageOrder.objects.create(
            user=request.user,
            destination=destination,
            num_days=num_days,
            num_people=num_people,
            num_rooms=num_rooms,
            vehicle=vehicle,
            food=food,
            accommodation=accommodation,
            guide=guide,
            bonfire=bonfire,
            total_price=total_price,
            per_person_price=per_person_price,
        )
        
        # Create admin notification
        AdminNotification.objects.create(
            notification_type='custom_package',
            title=f'New Custom Package Request #{order.order_number}',
            message=f'{request.user.username} has requested a custom tour package to {destination.title()} for {num_people} people, {num_days} days. Total: PKR {total_price:,.0f}',
            link=f'/admin/content/custompackageorder/{order.id}/change/',
            custom_package_order=order,
        )
        
        messages.success(request, f'Your custom package request #{order.order_number} has been submitted!')
        return redirect('content:custom_package_payment', order_id=order.id)
    
    return render(request, 'content/custom_package.html')


@login_required
def custom_package_payment(request, order_id):
    """Payment page for custom package using Stripe"""
    order = get_object_or_404(CustomPackageOrder, id=order_id, user=request.user)
    
    if order.payment_status == 'paid':
        messages.info(request, 'This package has already been paid for.')
        return redirect('content:custom_package_confirmation', order_id=order.id)
    
    context = {
        'order': order,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'content/custom_package_payment.html', context)


@login_required
def create_payment_intent(request, order_id):
    """Create Stripe PaymentIntent for custom package"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    order = get_object_or_404(CustomPackageOrder, id=order_id, user=request.user)
    
    if order.payment_status == 'paid':
        return JsonResponse({'error': 'Already paid'}, status=400)
    
    try:
        # Convert PKR to paisa (smallest unit) for Stripe
        amount_in_paisa = int(order.total_price * 100)
        
        # For testing: use a small amount (minimum 50 cents = $0.50 USD)
        # Since we're in test mode, we'll use USD with a converted small amount
        test_amount = max(50, min(amount_in_paisa, 99999999))  # Stripe minimum is 50 cents
        
        intent = stripe.PaymentIntent.create(
            amount=test_amount,
            currency='usd',  # Using USD for test mode compatibility
            metadata={
                'order_id': order.id,
                'order_number': order.order_number,
                'user_id': request.user.id,
                'destination': order.destination,
                'actual_amount_pkr': str(order.total_price),
            },
            description=f'Custom Package #{order.order_number} - {order.destination.title()}',
        )
        
        order.stripe_payment_intent_id = intent.id
        order.save()
        
        return JsonResponse({
            'clientSecret': intent.client_secret,
        })
    except Exception as e:
        logger.error(f"Stripe PaymentIntent creation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_success(request, order_id):
    """Handle successful payment"""
    order = get_object_or_404(CustomPackageOrder, id=order_id, user=request.user)
    
    if order.payment_status != 'paid':
        order.payment_status = 'paid'
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save()
        
        # Log successful payment
        log_security_event(
            'payment_success',
            request.user,
            {
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': str(order.total_price),
                'destination': order.destination
            },
            level='info'
        )
        
        # Notify admin about payment
        AdminNotification.objects.create(
            notification_type='payment',
            title=f'Payment Received for #{order.order_number}',
            message=f'Payment of PKR {order.total_price:,.0f} received from {request.user.username} for custom package to {order.destination.title()}.',
            link=f'/admin/content/custompackageorder/{order.id}/change/',
            custom_package_order=order,
        )
    
    return redirect('content:custom_package_confirmation', order_id=order.id)


@login_required
def custom_package_confirmation(request, order_id):
    """Order confirmation page for custom package"""
    order = get_object_or_404(CustomPackageOrder, id=order_id, user=request.user)
    return render(request, 'content/custom_package_confirmation.html', {'order': order})


@login_required
def my_custom_packages(request):
    """View user's custom package orders"""
    orders = CustomPackageOrder.objects.filter(user=request.user)
    return render(request, 'content/my_custom_packages.html', {'orders': orders})


@login_required
def admin_notifications_api(request):
    """API endpoint to get unread admin notifications (for admin users)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    notifications = AdminNotification.objects.filter(is_read=False)[:20]
    data = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notifications]
    
    return JsonResponse({'notifications': data, 'unread_count': AdminNotification.objects.filter(is_read=False).count()})


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    notification = get_object_or_404(AdminNotification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

# Cart and Order Views
@login_required
def add_to_cart(request, product_id):
    """Add product to cart (supports AJAX)"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not product.is_in_stock():
        if is_ajax:
            return JsonResponse({'success': False, 'message': f'{product.name} is out of stock.'})
        messages.error(request, f'{product.name} is out of stock.')
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('content:product_list')
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, product=product, defaults={'quantity': 1}
    )
    
    msg = ''
    if not item_created:
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
            msg = f'Added another {product.name} to cart.'
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Cannot add more {product.name}. Only {product.stock_quantity} available.'})
            messages.warning(request, f'Cannot add more {product.name}. Only {product.stock_quantity} available.')
    else:
        msg = f'{product.name} added to cart.'
    
    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': cart.get_items_count(),
        })
    
    messages.success(request, msg)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('content:product_list')

@login_required
def view_cart(request):
    """View shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all().select_related('product')
    
    total_weight = cart.get_total_weight()
    shipping_fee = cart.get_shipping_fee()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': cart.get_total(),
        'total_weight': total_weight,
        'shipping_fee': shipping_fee,
        'grand_total': cart.get_total() + shipping_fee,
    }
    
    return render(request, 'content/cart.html', context)

@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity (supports AJAX)"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        quantity = int(request.POST.get('quantity', 1))
        
        msg = ''
        success = True
        if quantity > 0:
            if quantity <= cart_item.product.stock_quantity:
                cart_item.quantity = quantity
                cart_item.save()
                msg = 'Cart updated.'
            else:
                msg = f'Only {cart_item.product.stock_quantity} items available.'
                success = False
        else:
            cart_item.delete()
            msg = 'Item removed from cart.'
        
        if is_ajax:
            cart = Cart.objects.get(user=request.user)
            return JsonResponse({
                'success': success,
                'message': msg,
                'item_subtotal': float(cart_item.get_subtotal()) if success and quantity > 0 else 0,
                'item_quantity': cart_item.quantity if success and quantity > 0 else 0,
                'cart_count': cart.get_items_count(),
                'subtotal': float(cart.get_total()),
                'total_weight': float(cart.get_total_weight()),
                'shipping_fee': float(cart.get_shipping_fee()),
                'grand_total': float(cart.get_total() + cart.get_shipping_fee()),
                'removed': quantity <= 0,
            })
        
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    
    return redirect('content:view_cart')

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart (supports AJAX)"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    cart_item.delete()
    
    if is_ajax:
        cart = Cart.objects.get(user=request.user)
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart.',
            'cart_count': cart.get_items_count(),
            'subtotal': float(cart.get_total()),
            'total_weight': float(cart.get_total_weight()),
            'shipping_fee': float(cart.get_shipping_fee()),
            'grand_total': float(cart.get_total() + cart.get_shipping_fee()),
        })
    
    messages.success(request, f'{product_name} removed from cart.')
    return redirect('content:view_cart')

@login_required
def checkout(request):
    """Checkout page"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all().select_related('product')
    
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('content:product_list')
    
    # Check stock availability
    for item in cart_items:
        if not item.product.is_in_stock():
            messages.error(request, f'{item.product.name} is out of stock.')
            return redirect('content:view_cart')
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f'Only {item.product.stock_quantity} {item.product.name} available.')
            return redirect('content:view_cart')
    
    shipping_fee = cart.get_shipping_fee()
    subtotal = cart.get_total()
    total = subtotal + shipping_fee
    total_weight = cart.get_total_weight()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
        'total_weight': total_weight,
    }
    
    return render(request, 'content/checkout.html', context)

@login_required
def place_order(request):
    """Place order"""
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        cart_items = cart.items.all().select_related('product')
        
        if not cart_items.exists():
            messages.error(request, 'Your cart is empty.')
            return redirect('content:product_list')
        
        # Validate bank transfer transaction ID
        payment_method = request.POST.get('payment_method', 'cod')
        if payment_method == 'bank_transfer':
            import re as re_mod
            txn_id = request.POST.get('transaction_id', '').strip()
            if not txn_id or not re_mod.match(r'^[A-Za-z0-9\-]{5,50}$', txn_id):
                messages.error(request, 'Please enter a valid Transaction ID (5-50 characters, letters, numbers & hyphens only).')
                return redirect('content:checkout')
        
        # Revalidate stock availability (race condition protection)
        for cart_item in cart_items:
            # Refresh from database to get current stock
            cart_item.product.refresh_from_db()
            if not cart_item.product.is_in_stock():
                messages.error(request, f'{cart_item.product.name} is out of stock. Please update your cart.')
                return redirect('content:view_cart')
            if cart_item.quantity > cart_item.product.stock_quantity:
                messages.error(request, f'Only {cart_item.product.stock_quantity} {cart_item.product.name} available. Please update your cart.')
                return redirect('content:view_cart')
        
        # Calculate totals with dynamic shipping
        shipping_fee = cart.get_shipping_fee()
        subtotal = cart.get_total()
        total = subtotal + shipping_fee
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            postal_code=request.POST.get('postal_code'),
            payment_method=request.POST.get('payment_method', 'cod'),
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total=total,
            notes=request.POST.get('notes', ''),
        )
        
        # Create order items and reduce stock atomically
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            
            # Reduce stock using F() expression (atomic operation)
            cart_item.product.stock_quantity = F('stock_quantity') - cart_item.quantity
            cart_item.product.save(update_fields=['stock_quantity'])
        
        # Clear cart
        cart_items.delete()
        
        # Log successful order placement
        log_security_event(
            'order_placed',
            request.user,
            {
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': str(total),
                'payment_method': payment_method,
                'items_count': len(cart_items)
            },
            level='info'
        )
        
        messages.success(request, f'Order #{order.order_number} placed successfully!')
        return redirect('content:order_confirmation', order_id=order.id)
    
    return redirect('content:checkout')

@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all().select_related('product')
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'content/order_confirmation.html', context)

@login_required
def my_orders(request):
    """View user's orders"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'content/my_orders.html', context)


@login_required
def add_product_review(request, product_id, order_id):
    """Add a review for a product after order delivery"""
    product = get_object_or_404(Product, id=product_id)
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Check that order is delivered
    if order.status != 'delivered':
        messages.error(request, 'You can only review products from delivered orders.')
        return redirect('content:my_orders')

    # Check that product is in this order
    if not order.items.filter(product=product).exists():
        messages.error(request, 'This product is not in your order.')
        return redirect('content:my_orders')

    # Check if already reviewed
    if ProductReview.objects.filter(user=request.user, product=product).exists():
        messages.info(request, 'You have already reviewed this product.')
        return redirect('content:product_list')

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
            return render(request, 'content/add_product_review.html', {
                'product': product,
                'order': order,
                'form_data': request.POST,
            })

        ProductReview.objects.create(
            user=request.user,
            product=product,
            rating=rating_val,
            title=title,
            comment=comment,
            is_verified_purchase=True,
        )

        messages.success(request, 'Thank you for your review!')
        return redirect('content:product_list')

    return render(request, 'content/add_product_review.html', {
        'product': product,
        'order': order,
    })

