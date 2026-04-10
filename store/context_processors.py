# store/context_processors.py

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.cart.item_count()
        except Exception:
            count = 0
    return {'cart_count': count}