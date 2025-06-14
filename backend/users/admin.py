from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import Subscription, User


class HasRecipesFilter(admin.SimpleListFilter):
    title = "Есть рецепты"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(recipes__isnull=True)


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "Есть подписки"
    parameter_name = "has_subscriptions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(subscriptions__isnull=True)


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "Есть подписчики"
    parameter_name = "has_subscribers"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Да"),
            ("no", "Нет"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                subscriptions_authors__isnull=False
            ).distinct()
        if self.value() == "no":
            return queryset.filter(subscriptions_authors__isnull=True)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_html",
        "recipe_count",
        "subscription_count",
        "subscriber_count",
        "is_staff",
    )

    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
        "is_active",
        "is_staff",
    )
    readonly_fields = ("id",)
    ordering = ("username",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipe_count=Count("recipes"),
            subscription_count=Count("subscriptions"),
            subscriber_count=Count("subscriptions_authors"),
        )

    @mark_safe
    def avatar_html(self, obj):
        if obj.avatar:
            return (
                f'<img src="{obj.avatar.url}"'
                ' width="30" height="30"'
                f' alt="{obj.username}">'
            )
        return "-"

    avatar_html.short_description = "Аватар"

    def full_name(self, obj):
        return obj.get_full_name()

    full_name.short_description = "Имя пользователя"

    def recipe_count(self, obj):
        return obj.recipes.count()

    recipe_count.short_description = "Кол-во рецептов"

    def subscription_count(self, obj):
        return obj.subscriptions.count()

    subscription_count.short_description = "Подписки"

    def subscriber_count(self, obj):
        return obj.subscriptions_authors.count()

    subscriber_count.short_description = "Подписчики"

    def has_recipes(self, obj):
        return obj.has_recipes > 0

    has_recipes.boolean = True
    has_recipes.short_description = "Есть рецепты"

    def has_subscriptions(self, obj):
        return obj.has_subscriptions > 0

    has_subscriptions.boolean = True
    has_subscriptions.short_description = "Есть подписки"

    def has_subscribers(self, obj):
        return obj.has_subscribers > 0

    has_subscribers.boolean = True
    has_subscribers.short_description = "Есть подписчики"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "author")
    list_filter = ("subscriber", "author")
    search_fields = ("subscriber__username", "author__username")
    empty_value_display = "-пусто-"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("subscriber", "author")
