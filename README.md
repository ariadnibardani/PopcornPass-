## Key Libraries Explained

### bleach
**What it is:** A Python library for sanitising (cleaning) user input.  
**What it does:** When a user types something into a form (like a review), bleach strips out any dangerous HTML tags like `<script>` before saving to the database.  
**Why we need it:** Without bleach, a malicious user could type `<script>alert('hacked')</script>` into a review field and attack other users — this is called Cross-Site Scripting (XSS).  
**Where it's used:** `store/security.py` → `sanitize_text()` function, called in all form `clean_` methods.

```python
# Example from store/security.py
import bleach
def sanitize_text(value):
    cleaned = bleach.clean(value, tags=[], attributes={}, strip=True)
    return cleaned.strip()
```

### Pillow
**What it is:** A Python imaging library.  
**What it does:** Handles image uploads — when staff upload a movie poster, Pillow processes and saves the image file correctly.  
**Why we need it:** Django's `ImageField` model field requires Pillow to be installed to handle image validation and storage.  
**Where it's used:** `store/models.py` → `Movie.poster` and `Director.photo` fields.

### django-crispy-forms
**What it is:** A Django library that renders forms beautifully.  
**What it does:** Automatically styles Django forms using Bootstrap 5 classes, saving us from writing HTML for every form field manually.  
**Why we need it:** Makes registration, login and profile forms look polished without extra HTML.  
**Where it's used:** All templates that use `{{ form|crispy }}` tag.

---

## Security Features

### SQL Injection Protection
Django's ORM (Object Relational Mapper) automatically escapes all database queries. We never write raw SQL — instead we write:
```python
Movie.objects.filter(title__icontains=query)
```
Django converts this safely, so even if a user types `' OR '1'='1`, it won't affect the database.

### XSS (Cross-Site Scripting) Protection
- All user input is sanitised using `bleach` before saving
- Django's template engine auto-escapes variables with `{{ variable }}`
- Custom `validate_no_script()` function blocks script tags in forms

### CSRF (Cross-Site Request Forgery) Protection
Every form includes `{% csrf_token %}` — a hidden token that verifies the request came from our site and not from a malicious external site.