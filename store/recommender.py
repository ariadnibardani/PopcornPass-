from django.db.models import Count
from .models import Movie, ViewHistory, Rating, OrderItem


def get_recommendations(user, limit=8):
    if not user.is_authenticated:
        return Movie.objects.filter(
            featured=True
        ).order_by('-created_at')[:limit]

    viewed_ids    = ViewHistory.objects.filter(
        user=user).values_list('movie_id', flat=True)
    rated_ids     = Rating.objects.filter(
        user=user).values_list('movie_id', flat=True)
    purchased_ids = OrderItem.objects.filter(
        order__user=user).values_list('movie_id', flat=True)

    exclude_ids = set(list(viewed_ids) + list(rated_ids) + list(purchased_ids))

    viewed_genres = ViewHistory.objects.filter(
        user=user
    ).values('movie__genre').annotate(
        c=Count('id')
    ).order_by('-c').values_list('movie__genre', flat=True)[:4]

    liked_genres = Rating.objects.filter(
        user=user, score__gte=4
    ).values('movie__genre').annotate(
        c=Count('id')
    ).order_by('-c').values_list('movie__genre', flat=True)[:3]

    preferred = list(dict.fromkeys(
        list(viewed_genres) + list(liked_genres)
    ))

    recommendations = []

    for genre_id in preferred:
        if len(recommendations) >= limit:
            break
        picks = Movie.objects.filter(
            genre_id=genre_id
        ).exclude(
            id__in=exclude_ids
        ).exclude(
            id__in=[m.id for m in recommendations]
        ).order_by('-featured', '-release_year')[:3]
        recommendations.extend(list(picks))

    if len(recommendations) < limit:
        fallback = Movie.objects.exclude(
            id__in=exclude_ids
        ).exclude(
            id__in=[m.id for m in recommendations]
        ).filter(featured=True).order_by('-created_at')
        recommendations.extend(
            list(fallback[:limit - len(recommendations)])
        )

    if len(recommendations) < limit:
        final = Movie.objects.exclude(
            id__in=exclude_ids
        ).exclude(
            id__in=[m.id for m in recommendations]
        ).order_by('-release_year')
        recommendations.extend(
            list(final[:limit - len(recommendations)])
        )

    return recommendations[:limit]

def get_similar_movies(movie, limit=4):
    """
    Returns movies that are genuinely similar —
    same genre OR same director, never the same movie,
    never movies from completely different genres.
    """
    results = []

    # First priority: same director, different movie
    by_director = list(
        Movie.objects.filter(
            director=movie.director
        ).exclude(
            id=movie.id
        ).order_by('-release_year')[:2]
    )
    results.extend(by_director)

    # Second priority: same genre, not already included
    already_ids = [m.id for m in results] + [movie.id]
    by_genre = list(
        Movie.objects.filter(
            genre=movie.genre
        ).exclude(
            id__in=already_ids
        ).order_by('-featured', '-release_year')[:limit - len(results)]
    )
    results.extend(by_genre)

    # Final fallback: same decade if still not enough
    if len(results) < limit:
        already_ids = [m.id for m in results] + [movie.id]
        by_decade = list(
            Movie.objects.filter(
                decade=movie.decade
            ).exclude(
                id__in=already_ids
            ).order_by('-release_year')[:limit - len(results)]
        )
        results.extend(by_decade)

    return results[:limit]