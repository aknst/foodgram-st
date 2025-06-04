from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Subscription(models.Model):
    """Model to represent user subscriptions"""

    subscriber = models.ForeignKey(
        "User",
        related_name="subscriptions",
        on_delete=models.CASCADE,
        verbose_name=_("subscriber"),
    )
    author = models.ForeignKey(
        "User",
        related_name="subscribers",
        on_delete=models.CASCADE,
        verbose_name=_("author"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")
        unique_together = ("subscriber", "author")
        constraints = [
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F("author")),
                name="prevent_self_subscription",
            )
        ]

    def __str__(self):
        return f"{self.subscriber} -> {self.author}"


class User(AbstractUser):
    """Custom user model with email as username field"""

    email = models.EmailField(
        _("email address"),
        unique=True,
        max_length=254,
        help_text=_(
            "Required. 254 characters or fewer. Must be a valid email address."
        ),
    )
    username = models.CharField(
        _("username"),
        max_length=150,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
    )
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("username",)

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}"

    def get_latest_recipes(self, limit=3):
        """Get latest recipes of the user with limited fields"""
        from recipes.models import Recipe

        return Recipe.objects.filter(author=self)[: limit if limit else 3]
