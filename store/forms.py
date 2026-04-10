from django import forms
from .models import Movie, Genre, Director
from .security import sanitize_text, validate_no_script


class MovieForm(forms.ModelForm):
    class Meta:
        model  = Movie
        fields = [
            'title', 'slug', 'director', 'genre', 'decade',
            'description', 'imdb_id', 'rental_price', 'stock',
            'poster', 'language', 'studio', 'release_year',
            'runtime', 'featured', 'keywords'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'slug': forms.TextInput(
                attrs={'placeholder': 'auto-fills from title'}
            ),
        }

    def clean_title(self):
        value = self.cleaned_data.get('title', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_description(self):
        value = self.cleaned_data.get('description', '')
        validate_no_script(value)
        return sanitize_text(value)


class GenreForm(forms.ModelForm):
    class Meta:
        model  = Genre
        fields = ['name', 'slug', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'slug': forms.TextInput(
                attrs={'placeholder': 'auto-fills from name'}
            ),
        }

    def clean_name(self):
        value = self.cleaned_data.get('name', '')
        validate_no_script(value)
        return sanitize_text(value)


class DirectorForm(forms.ModelForm):
    class Meta:
        model  = Director
        fields = ['name', 'bio', 'photo']
        widgets = {'bio': forms.Textarea(attrs={'rows': 3})}

    def clean_name(self):
        value = self.cleaned_data.get('name', '')
        validate_no_script(value)
        return sanitize_text(value)