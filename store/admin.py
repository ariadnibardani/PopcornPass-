from django.contrib import admin
from .models import (
    Movie, Genre, Decade, Director, UserProfile,
    Cart, CartItem, Order, OrderItem,
    Rating, Watchlist, ViewHistory
)

# Register models here

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'director', 'genre',
                    'decade', 'rental_price', 'featured']
    list_editable = ['rental_price', 'featured']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'imdb_id']
    list_filter = ['genre', 'decade', 'language', 'featured']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Decade)
class DecadeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'start_year', 'end_year']


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Rating)
admin.site.register(Watchlist)
admin.site.register(ViewHistory)