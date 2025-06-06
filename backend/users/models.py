from django.contrib.auth.models import AbstractUser
from django.db import models


class Subscription(models.Model):
    """Model to represent user subscriptions"""

    subscriber = models.ForeignKey(
        "User",
        related_name="subscriptions",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        "User",
        related_name="subscribers",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
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
    email = models.EmailField(
        "Адрес эл. почты",
        unique=True,
        max_length=254,
        help_text=(
            "Обязательно. Не более 254 символов. "
            "Должен быть действительным адресом эл. почты."
        ),
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=150,
        help_text=(
            "Обязательно. Не более 150 символов. "
            "Буквы, цифры и символы @/./+/-/_ только."
        ),
    )
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField(
        "Аватар", upload_to="avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_latest_recipes(self, limit=3):
        return self.recipes.all()[: limit if limit else 3]
