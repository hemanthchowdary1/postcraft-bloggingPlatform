from django import forms
from .models import Comment, Post
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment…'})
        }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    # No validators, no help text — just enter what you want
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password'}),
        help_text=None,
        validators=[],
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        help_text=None,
        validators=[],
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def _post_clean(self):
        # Bypass Django's built-in password strength validators
        super()._post_clean()
        self._errors.pop('password2', None)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match.")
        return p2


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "image", "tags"]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Write your post content…'}),
            'title': forms.TextInput(attrs={'placeholder': 'Enter a compelling title…'}),
            'tags': forms.TextInput(attrs={'placeholder': 'python, django, web (comma separated)'}),
        }


class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "image", "tags"]
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
            'tags': forms.TextInput(attrs={'placeholder': 'python, django, web (comma separated)'}),
        }


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
        }