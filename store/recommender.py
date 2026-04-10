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
    by_director = Movie.objects.filter(
        director=movie.director
    ).exclude(id=movie.id).order_by('-release_year')[:2]

    dir_ids = [m.id for m in by_director]

    by_genre = Movie.objects.filter(
        genre=movie.genre
    ).exclude(id=movie.id).exclude(
        id__in=dir_ids
    ).order_by('-featured', '-release_year')[:limit - len(dir_ids)]

    result = list(by_director) + list(by_genre)

    if len(result) < limit:
        more = Movie.objects.exclude(
            id=movie.id
        ).exclude(
            id__in=[m.id for m in result]
        ).order_by('?')[:limit - len(result)]
        result.extend(list(more))

    return result[:limit]