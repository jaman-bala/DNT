from django.db import models
from django.utils import timezone

from apps.user.managers import UserManager
from apps.user.utils.password import is_password_change_required
from config.base.base_model import BaseAuthModel


class User(BaseAuthModel):
    first_name = models.CharField("First name", max_length=150, blank=True, null=True)
    last_name = models.CharField("Last name", max_length=150, blank=True, null=True)
    middle_name = models.CharField("Middle name", max_length=150, blank=True, null=True)
    email = models.EmailField("Email", blank=True, null=True)
    phone = models.CharField("Phone", max_length=15, unique=True)
    profile_image = models.ImageField("Profile image", blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    can_activate = models.BooleanField("Can Activate", default=False)
    date_joined = models.DateTimeField("Date joined", default=timezone.now)
    last_login = models.DateTimeField("Last login", blank=True, null=True)
    password_changed_at = models.DateTimeField(
        "Password changed at", default=timezone.now
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # type: ignore
    objects = UserManager()

    def __str__(self) -> str:
        return f"{self.phone} - {self.get_full_name()}"

    def get_full_name(self) -> str:
        """Return the full name for the user."""
        names = [self.last_name, self.first_name, self.middle_name]
        return " ".join([name for name in names if name]).strip() or self.phone

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        return self.phone

    @property
    def password_change_required(self) -> bool:
        """Returns True if the user is required to change their password."""
        return is_password_change_required(self)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = "users"
