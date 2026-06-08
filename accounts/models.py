from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal


from .utils import create_otp
import stripe


class CustomUserManager(BaseUserManager):
    """User manager that works with email‑only authentication."""
    use_in_migrations = True

    def get_queryset(self):
        print("query form manager....")
        return super().get_queryset().prefetch_related(
            "likes__movies", "likes__series"
        )

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        print("____create")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        print("create user.....")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

def upload_to(instance, filename):
    return f"user_{instance.id}_{filename}"

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    profile_image = models.ImageField(upload_to=upload_to, null=True, blank=True, verbose_name='profile_images')
    full_name = models.CharField(max_length=255, default="", blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True, choices=[
        ("Male", "Male"),
        ("Female", "Female"),
        ('Disabled', 'Disabled')
    ])
    date_of_birth = models.DateField(null=True, blank=True)

    phone = models.CharField(max_length=20, default="")
    country = models.CharField(max_length=100, default="")
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)

    otp = models.CharField(default=create_otp, max_length=10)

    email_verified = models.BooleanField(default=False)
    language = models.CharField(max_length=10, choices=(
        ("en_US", "en_US"),
        ("fr_FR", "fr_FR"),
        ("es_ES", "es_ES"),
    ), default="en_US")

    device_token = models.CharField(max_length=150, default="")
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        print("hey........")
        if not hasattr(self, 'profile_image'):
            return
        try:
            img = Image.open(self.profile_image.path)
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return
        if img.height < 300 and img.width < 300:
            if os.path.exists(self.profile_image.path):
                os.remove(self.profile_image.path)
            raise ValidationError("image minimum size must be >300x300")
        output_size = (300, 300)
        img.thumbnail(output_size)
        img.save(self.profile_image.path)

    @property
    def get_full_name(self):
        pass


class SiteConfig(models.Model):
    subscription_price_id = models.CharField(max_length=100, null=True)
    moncash_subscription_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal(0.0),
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    yearly_subscription_price_id = models.CharField(max_length=100, null=True)
    yearly_moncash_subscription_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal(0.0),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    privacy_policy = models.TextField(default="")

    def full_clean(self, exclude, validate_unique=False):
        if self.subscription_price_id:
            try:
                stripe.Price.retrieve(self.subscription_price_id)
            except stripe._error.InvalidRequestError as e:
                raise ValidationError(str(e))


class HelpSupport(models.Model):
    email = models.EmailField()
    description = models.TextField()

    answer = models.TextField(default="", blank=True)
    is_solved = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:20]