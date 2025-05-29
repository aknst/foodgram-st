from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom user model with email as username field"""
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        max_length=254,
        help_text=_('Required. 254 characters or fewer. Must be a valid email address.')
    )
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    first_name = models.CharField(
        _('first name'),
        max_length=150
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('username',)

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}"
