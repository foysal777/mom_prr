from django.db import models
from django.contrib.auth import get_user_model
import datetime


UserModel = get_user_model()


class Subscription(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE,
                                related_name='subscription')
    stripe_subscription_id = models.CharField(
        max_length=200, unique=True,
        null=True, blank=True, default=None
    )

    purchase_date = models.DateTimeField(null=True, blank=True)
    period = models.CharField(choices=(
        ('monthly', 'monthly'),
        ('yearly', 'yearly')
    ), null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    subscribe_till = models.DateTimeField(null=True, blank=True)

    @property
    def remaining_time(self):
        if not self.subscribe_till:
            return datetime.timedelta()
        t_delta = self.subscribe_till - datetime.datetime.now(datetime.timezone.utc)
        return t_delta if t_delta > datetime.timedelta() else datetime.timedelta()

    def set_subscribe(self, period):
        # self.s_type = s_type

        # t_delta = datetime.timedelta(days=30 if s_type == 'monthly' else 365)
        print("increasing sub time")
        t_delta = datetime.timedelta(
            days=30 if period == 'monthly' else 365
        )
        self.period=period
        self.purchase_date = datetime.datetime.now()
        self.subscribe_till = datetime.datetime.now(datetime.timezone.utc) \
            + self.remaining_time + t_delta
        # print(self.subscribe_till)