from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                               views.home,              name='home'),
    path('movies/',                        views.catalogue,         name='catalogue'),
    path('movies/<slug:slug>/',            views.movie_detail,      name='movie_detail'),
    path('watchlist/<int:movie_id>/',      views.toggle_watchlist,  name='toggle_watchlist'),

    # Ratings
    path('movies/<int:movie_id>/rate/',        views.rate_movie,    name='rate_movie'),
    path('movies/<int:movie_id>/rate/delete/', views.delete_rating, name='delete_rating'),

    # Recommendations
    path('for-you/', views.recommendations_page, name='recommendations'),

    # Cart / Rent
    path('cart/',                          views.cart_detail,       name='cart_detail'),
    path('cart/add/<int:movie_id>/',       views.add_to_cart,       name='add_to_cart'),
    path('cart/remove/<int:item_id>/',     views.remove_from_cart,  name='remove_from_cart'),
    path('cart/update/<int:item_id>/',     views.update_cart,       name='update_cart'),
    path('cart/checkout/',                 views.checkout,          name='checkout'),
    path('order/<int:order_id>/confirm/',  views.order_confirmation,name='order_confirmation'),

    # Site Admin
    path('site-admin/',                            views.site_admin_dashboard, name='site_admin_dashboard'),
    path('site-admin/movies/',                     views.admin_movie_list,     name='admin_movie_list'),
    path('site-admin/movies/add/',                 views.admin_movie_add,      name='admin_movie_add'),
    path('site-admin/movies/<int:movie_id>/edit/', views.admin_movie_edit,     name='admin_movie_edit'),
    path('site-admin/movies/<int:movie_id>/delete/', views.admin_movie_delete, name='admin_movie_delete'),
    path('site-admin/genres/',                     views.admin_genre_list,     name='admin_genre_list'),
    path('site-admin/genres/add/',                 views.admin_genre_add,      name='admin_genre_add'),
    path('site-admin/genres/<int:genre_id>/edit/', views.admin_genre_edit,     name='admin_genre_edit'),
    path('site-admin/genres/<int:genre_id>/delete/', views.admin_genre_delete, name='admin_genre_delete'),
    path('site-admin/users/',                      views.admin_user_list,      name='admin_user_list'),
    path('site-admin/users/<int:user_id>/toggle-staff/', views.admin_user_toggle_staff, name='admin_user_toggle_staff'),
    path('site-admin/users/<int:user_id>/delete/', views.admin_user_delete,    name='admin_user_delete'),
    path('site-admin/orders/',                     views.admin_order_list,     name='admin_order_list'),
    path('site-admin/orders/<int:order_id>/',      views.admin_order_detail,   name='admin_order_detail'),
]