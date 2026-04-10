from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from store.models import UserProfile, ViewHistory, Order, Watchlist, Rating
from .forms import RegisterForm, UpdateUserForm, UpdateProfileForm
from django.db.models import Avg

# Create your views here.

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile and cart automatically
            UserProfile.objects.create(user=user)
            from store.models import Cart
            Cart.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to PopcornPass, {user.first_name}!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            from store.security import safe_redirect_url
            next_url = safe_redirect_url(request.GET.get('next', ''), fallback='/')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    # Create profile/cart if they don't exist (safety net)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    from store.models import Cart
    Cart.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form    = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form    = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=profile)

    return render(request, 'users/profile.html', {
        'user_form':    user_form,
        'profile_form': profile_form,
    })


@login_required
def dashboard_view(request):
    from store.models import ViewHistory, Order, Watchlist, Rating
    user = request.user

    recent_views  = ViewHistory.objects.filter(
        user=user
    ).select_related('movie').order_by('-viewed_at')[:6]

    recent_orders = Order.objects.filter(
        user=user
    ).order_by('-created_at')[:5]

    watchlist = Watchlist.objects.filter(
        user=user
    ).select_related('movie').order_by('-added')[:6]

    ratings = Rating.objects.filter(
        user=user
    ).select_related('movie').order_by('-created')[:5]

    return render(request, 'users/dashboard.html', {
        'recent_views':  recent_views,
        'recent_orders': recent_orders,
        'watchlist':     watchlist,
        'ratings':       ratings,
    })