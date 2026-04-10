from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


# ─── GENRE ───────────────────────────────────────────────────

class Genre(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ─── DECADE ──────────────────────────────────────────────────

class Decade(models.Model):
    name  = models.CharField(max_length=20)   # e.g. "1980s"
    slug  = models.SlugField(unique=True)      # e.g. "1980s"
    start_year = models.IntegerField()         # e.g. 1980
    end_year   = models.IntegerField()         # e.g. 1989

    class Meta:
        ordering = ['start_year']

    def __str__(self):
        return self.name


# ─── DIRECTOR ────────────────────────────────────────────────

class Director(models.Model):
    name  = models.CharField(max_length=200)
    bio   = models.TextField(blank=True)
    photo = models.ImageField(upload_to='directors/', blank=True, null=True)

    def __str__(self):
        return self.name


# ─── MOVIE ───────────────────────────────────────────────────

class Movie(models.Model):
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('JA', 'Japanese'),
        ('KO', 'Korean'),
    ]

    title        = models.CharField(max_length=255)
    slug         = models.SlugField(unique=True)
    director     = models.ForeignKey(
        Director, on_delete=models.CASCADE, related_name='movies'
    )
    genre        = models.ForeignKey(
        Genre, on_delete=models.SET_NULL, null=True, related_name='movies'
    )
    decade       = models.ForeignKey(
        Decade, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movies'
    )
    description  = models.TextField()
    imdb_id      = models.CharField(max_length=20, unique=True, blank=True)
    rental_price = models.DecimalField(max_digits=6, decimal_places=2)
    stock        = models.PositiveIntegerField(default=10)
    poster       = models.ImageField(upload_to='movies/', blank=True, null=True)
    language     = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default='EN'
    )
    studio       = models.CharField(max_length=200, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    runtime      = models.PositiveIntegerField(
        null=True, blank=True, help_text='Runtime in minutes'
    )
    featured     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    keywords = models.TextField(
    blank=True,
    help_text='Comma-separated keywords e.g. dinosaurs, time travel, space'
    )

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.score for r in ratings) / ratings.count(), 1)
        return 0

    def is_available(self):
        return self.stock > 0

    def runtime_display(self):
        if not self.runtime:
            return 'N/A'
        hours   = self.runtime // 60
        minutes = self.runtime % 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


# ─── USER PROFILE ────────────────────────────────────────────

class UserProfile(models.Model):
    user       = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio        = models.TextField(blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    address    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# ─── WATCHLIST ───────────────────────────────────────────────

class Watchlist(models.Model):
    user  = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='watchlist'
    )
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} → {self.movie.title}"


# ─── RATING ──────────────────────────────────────────────────

class Rating(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    movie   = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name='ratings'
    )
    score   = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review  = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.score}/5"


# ─── VIEW HISTORY (for recommender) ──────────────────────────

class ViewHistory(models.Model):
    user      = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='view_history'
    )
    movie     = models.ForeignKey(Movie, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering        = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.movie.title}"


# ─── CART ────────────────────────────────────────────────────

class Cart(models.Model):
    user       = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s cart"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart     = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items'
    )
    movie    = models.ForeignKey(Movie, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.movie.rental_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.movie.title}"


# ─── ORDER ───────────────────────────────────────────────────

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('active',    'Rental Active'),
        ('returned',  'Returned'),
    ]

    user       = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders'
    )
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total      = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order    = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    movie    = models.ForeignKey(Movie, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price    = models.DecimalField(max_digits=8, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity