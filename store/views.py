from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
import json

from .models import (Movie, Genre, Decade, Director, Cart, CartItem,
                     Watchlist, ViewHistory, Rating, Order, OrderItem)
from .forms import MovieForm, GenreForm, DirectorForm
from .security import sanitize_text, validate_no_script, safe_redirect_url


# ─── HELPERS ─────────────────────────────────────────────────

def staff_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/users/login/?next={request.path}')
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── HOME ────────────────────────────────────────────────────

def home(request):
    from .recommender import get_recommendations
    featured = Movie.objects.filter(
        featured=True
    ).order_by('-created_at')[:8]
    genres  = Genre.objects.all().order_by('name')
    decades = Decade.objects.all().order_by('start_year')
    recommended = get_recommendations(request.user, limit=4)

    return render(request, 'store/home.html', {
        'featured':    featured,
        'genres':      genres,
        'decades':     decades,
        'recommended': recommended,
    })


# ─── CATALOGUE ───────────────────────────────────────────────

def catalogue(request):
    from django.db.models import Min, Max

    movies  = Movie.objects.all().select_related('director', 'genre', 'decade')
    genres  = Genre.objects.all().order_by('name')
    decades = Decade.objects.all().order_by('start_year')

    # Get actual min/max from database
    price_stats = Movie.objects.aggregate(
        min_price=Min('rental_price'),
        max_price=Max('rental_price')
    )
    year_stats = Movie.objects.aggregate(
        min_year=Min('release_year'),
        max_year=Max('release_year')
    )

    db_min_price = float(price_stats['min_price'] or 0)
    db_max_price = float(price_stats['max_price'] or 999)
    db_min_year  = int(year_stats['min_year'] or 1900)
    db_max_year  = int(year_stats['max_year'] or 2030)

    # Filter by genre
    genre_slug     = request.GET.get('genre')
    selected_genre = None
    if genre_slug:
        selected_genre = get_object_or_404(Genre, slug=genre_slug)
        movies = movies.filter(genre=selected_genre)

    # Filter by decade
    decade_slug     = request.GET.get('decade')
    selected_decade = None
    if decade_slug:
        selected_decade = get_object_or_404(Decade, slug=decade_slug)
        movies = movies.filter(decade=selected_decade)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        movies = movies.filter(
            Q(title__icontains=q)       |
            Q(director__name__icontains=q) |
            Q(studio__icontains=q)      |
            Q(description__icontains=q) |
            Q(keywords__icontains=q)    |
            Q(genre__name__icontains=q)
        )

    # Advanced filters with validation
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    language  = request.GET.get('language', '').strip()
    year_from = request.GET.get('year_from', '').strip()
    year_to   = request.GET.get('year_to', '').strip()

    if min_price:
        try:
            min_val = max(float(min_price), db_min_price)
            movies  = movies.filter(rental_price__gte=min_val)
        except ValueError:
            pass

    if max_price:
        try:
            max_val = min(float(max_price), db_max_price)
            movies  = movies.filter(rental_price__lte=max_val)
        except ValueError:
            pass

    if language:
        valid_langs = [code for code, _ in Movie.LANGUAGE_CHOICES]
        if language in valid_langs:
            movies = movies.filter(language=language)

    if year_from:
        try:
            yr = max(int(year_from), db_min_year)
            movies = movies.filter(release_year__gte=yr)
        except ValueError:
            pass

    if year_to:
        try:
            yr = min(int(year_to), db_max_year)
            movies = movies.filter(release_year__lte=yr)
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get('sort', 'title')
    sort_options = {
        'title':      'title',
        'price_asc':  'rental_price',
        'price_desc': '-rental_price',
        'newest':     '-release_year',
        'oldest':     'release_year',
    }
    movies = movies.order_by(sort_options.get(sort, 'title'))

    return render(request, 'store/catalogue.html', {
        'movies':           movies,
        'genres':           genres,
        'decades':          decades,
        'selected_genre':   selected_genre,
        'selected_decade':  selected_decade,
        'q':                q,
        'sort':             sort,
        'language_choices': Movie.LANGUAGE_CHOICES,
        'db_min_price':     db_min_price,
        'db_max_price':     db_max_price,
        'db_min_year':      db_min_year,
        'db_max_year':      db_max_year,
    })

# ─── MOVIE DETAIL ────────────────────────────────────────────

def movie_detail(request, slug):
    from .recommender import get_similar_movies
    movie       = get_object_or_404(Movie, slug=slug)
    ratings     = movie.ratings.select_related('user').order_by('-created')
    avg_rating  = ratings.aggregate(Avg('score'))['score__avg'] or 0
    user_rating = None
    in_watchlist = False

    if request.user.is_authenticated:
        ViewHistory.objects.update_or_create(
            user=request.user, movie=movie
        )
        try:
            user_rating = Rating.objects.get(
                user=request.user, movie=movie
            )
        except Rating.DoesNotExist:
            pass
        in_watchlist = Watchlist.objects.filter(
            user=request.user, movie=movie
        ).exists()

    similar = get_similar_movies(movie, limit=4)

    return render(request, 'store/movie_detail.html', {
        'movie':        movie,
        'ratings':      ratings,
        'avg_rating':   round(avg_rating, 1),
        'user_rating':  user_rating,
        'in_watchlist': in_watchlist,
        'similar':      similar,
    })


# ─── WATCHLIST ───────────────────────────────────────────────

@login_required
def toggle_watchlist(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    obj, created = Watchlist.objects.get_or_create(
        user=request.user, movie=movie
    )
    if not created:
        obj.delete()
        messages.info(request, f'"{movie.title}" removed from watchlist.')
    else:
        messages.success(request, f'"{movie.title}" added to watchlist!')
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


# ─── CART / RENT ─────────────────────────────────────────────

@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, movie=movie)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{movie.title}" added to rental cart!')
    return redirect(request.META.get('HTTP_REFERER', 'catalogue'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('cart_detail')


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    qty  = int(request.POST.get('quantity', 1))
    if qty < 1:
        item.delete()
    else:
        item.quantity = qty
        item.save()
    return redirect('cart_detail')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Your rental cart is empty.')
        return redirect('cart_detail')

    order = Order.objects.create(user=request.user, total=cart.total())
    for item in cart.items.all():
        OrderItem.objects.create(
            order    = order,
            movie    = item.movie,
            quantity = item.quantity,
            price    = item.movie.rental_price
        )
        item.movie.stock -= item.quantity
        item.movie.save()

    cart.items.all().delete()
    messages.success(request, f'Rental order #{order.id} confirmed!')
    return redirect('order_confirmation', order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


# ─── RATINGS ─────────────────────────────────────────────────

@login_required
def rate_movie(request, movie_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    movie = get_object_or_404(Movie, id=movie_id)

    try:
        data   = json.loads(request.body)
        score  = int(data.get('score', 0))
        review = data.get('review', '').strip()
    except (ValueError, KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse({'error': 'Score must be 1–5'}, status=400)

    try:
        validate_no_script(review)
    except Exception:
        return JsonResponse({'error': 'Invalid content in review.'}, status=400)

    review = sanitize_text(review)
    if len(review) > 1000:
        return JsonResponse({'error': 'Review too long (max 1000 chars).'}, status=400)

    rating, created = Rating.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={'score': score, 'review': review}
    )

    avg = movie.ratings.aggregate(Avg('score'))['score__avg'] or 0

    return JsonResponse({
        'success':  True,
        'created':  created,
        'score':    score,
        'review':   review,
        'avg':      round(avg, 1),
        'count':    movie.ratings.count(),
        'username': request.user.username,
    })


@login_required
def delete_rating(request, movie_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    movie  = get_object_or_404(Movie, id=movie_id)
    rating = Rating.objects.filter(user=request.user, movie=movie).first()
    if rating:
        rating.delete()
        avg = movie.ratings.aggregate(Avg('score'))['score__avg'] or 0
        return JsonResponse({
            'success': True,
            'avg':     round(avg, 1),
            'count':   movie.ratings.count(),
        })
    return JsonResponse({'error': 'No rating found'}, status=404)


# ─── RECOMMENDATIONS ─────────────────────────────────────────

@login_required
def recommendations_page(request):
    from .recommender import get_recommendations
    from django.db.models import Count

    history = ViewHistory.objects.filter(
        user=request.user
    ).select_related('movie__genre').order_by('-viewed_at')[:10]

    top_genres = ViewHistory.objects.filter(
        user=request.user
    ).values('movie__genre__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    recommendations = get_recommendations(request.user, limit=12)

    return render(request, 'store/recommendations.html', {
        'recommendations': recommendations,
        'history':         history,
        'top_genres':      top_genres,
    })


# ─── SITE ADMIN ──────────────────────────────────────────────

@staff_required
def site_admin_dashboard(request):
    total_movies  = Movie.objects.count()
    total_users   = User.objects.count()
    total_orders  = Order.objects.count()
    total_genres  = Genre.objects.count()
    recent_orders = Order.objects.select_related(
        'user'
    ).order_by('-created_at')[:8]

    return render(request, 'store/admin/dashboard.html', {
        'total_movies':  total_movies,
        'total_users':   total_users,
        'total_orders':  total_orders,
        'total_genres':  total_genres,
        'recent_orders': recent_orders,
    })


@staff_required
def admin_movie_list(request):
    movies = Movie.objects.select_related(
        'director', 'genre', 'decade'
    ).order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        movies = movies.filter(
            Q(title__icontains=q) | Q(director__name__icontains=q)
        )
    return render(request, 'store/admin/movie_list.html', {
        'movies': movies, 'q': q
    })


@staff_required
def admin_movie_add(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Movie added!')
            return redirect('admin_movie_list')
    else:
        form = MovieForm()
    return render(request, 'store/admin/movie_form.html', {
        'form': form, 'action': 'Add Movie'
    })


@staff_required
def admin_movie_edit(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{movie.title}" updated.')
            return redirect('admin_movie_list')
    else:
        form = MovieForm(instance=movie)
    return render(request, 'store/admin/movie_form.html', {
        'form': form, 'action': f'Edit: {movie.title}'
    })


@staff_required
def admin_movie_delete(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        title = movie.title
        movie.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('admin_movie_list')
    return render(request, 'store/admin/confirm_delete.html', {
        'object': movie, 'type': 'Movie'
    })


@staff_required
def admin_genre_list(request):
    genres = Genre.objects.all().order_by('name')
    return render(request, 'store/admin/genre_list.html', {'genres': genres})


@staff_required
def admin_genre_add(request):
    if request.method == 'POST':
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Genre added!')
            return redirect('admin_genre_list')
    else:
        form = GenreForm()
    return render(request, 'store/admin/genre_form.html', {
        'form': form, 'action': 'Add Genre'
    })


@staff_required
def admin_genre_edit(request, genre_id):
    genre = get_object_or_404(Genre, id=genre_id)
    if request.method == 'POST':
        form = GenreForm(request.POST, instance=genre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Genre updated!')
            return redirect('admin_genre_list')
    else:
        form = GenreForm(instance=genre)
    return render(request, 'store/admin/genre_form.html', {
        'form': form, 'action': f'Edit: {genre.name}'
    })


@staff_required
def admin_genre_delete(request, genre_id):
    genre = get_object_or_404(Genre, id=genre_id)
    if request.method == 'POST':
        genre.delete()
        messages.success(request, 'Genre deleted.')
        return redirect('admin_genre_list')
    return render(request, 'store/admin/confirm_delete.html', {
        'object': genre, 'type': 'Genre'
    })


@staff_required
def admin_user_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'store/admin/user_list.html', {'users': users})


@staff_required
def admin_user_toggle_staff(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    target = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if target.is_superuser:
            messages.error(request, 'Cannot modify a superuser.')
        else:
            target.is_staff = not target.is_staff
            target.save()
            status = 'granted staff to' if target.is_staff else 'revoked staff from'
            messages.success(request, f'Successfully {status} {target.username}.')
    return redirect('admin_user_list')


@staff_required
def admin_user_delete(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    target = get_object_or_404(User, id=user_id)
    if target.is_superuser:
        messages.error(request, 'Cannot delete a superuser.')
        return redirect('admin_user_list')
    if request.method == 'POST':
        target.delete()
        messages.success(request, 'User deleted.')
        return redirect('admin_user_list')
    return render(request, 'store/admin/confirm_delete.html', {
        'object': target, 'type': 'User'
    })


@staff_required
def admin_order_list(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    return render(request, 'store/admin/order_list.html', {'orders': orders})


@staff_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} updated.')
    return render(request, 'store/admin/order_detail.html', {'order': order})