from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.user.models.users import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Unfold's themed forms — without these, UserAdmin falls back to plain
    # Django's UserChangeForm/UserCreationForm, which work but look
    # unstyled/out of place next to the rest of the Unfold-skinned admin.
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "phone",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "email_verified",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "email_verified")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "middle_name",
                    "email",
                    "email_verified",
                    "profile_image",
                )
            },
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "can_activate")},
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "password_changed_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "password1", "password2"),
            },
        ),
    )
