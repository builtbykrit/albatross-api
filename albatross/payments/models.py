from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from drfstripe.models import CurrentSubscription as CurrentSubscriptionSuper
from drfstripe.models import Customer as CustomerSuper
from drfstripe.utils import convert_amount_for_db, convert_tstamp
from teams.models import Team

from .conf import settings as app_settings


plan_from_stripe_id = app_settings.plan_from_stripe_id


class CurrentSubscription(CurrentSubscriptionSuper):
    team = models.OneToOneField(
        Team,
        related_name='current_subscription',
        null=True
    )


class Customer(CustomerSuper):
    def sync_current_subscription(self, cu=None):
        cu = cu or self.stripe_customer
        sub = getattr(cu, "subscription", None)
        if sub is None:
            try:
                self.current_subscription.delete()
            except CurrentSubscription.DoesNotExist:
                pass
        else:
            try:
                sub_obj = self.current_subscription
                sub_obj.plan = plan_from_stripe_id(sub.plan.id)
                sub_obj.current_period_start = convert_tstamp(
                    sub.current_period_start
                )
                sub_obj.current_period_end = convert_tstamp(
                    sub.current_period_end
                )
                sub_obj.amount = convert_amount_for_db(sub.plan.amount, sub.plan.currency)
                sub_obj.currency = sub.plan.currency
                sub_obj.status = sub.status
                sub_obj.cancel_at_period_end = sub.cancel_at_period_end
                sub_obj.start = convert_tstamp(sub.start)
                sub_obj.quantity = sub.quantity
                sub_obj.save()
            except (CurrentSubscription.DoesNotExist, ObjectDoesNotExist):
                sub_obj = CurrentSubscription.objects.create(
                    customer=self,
                    plan=plan_from_stripe_id(sub.plan.id),
                    current_period_start=convert_tstamp(
                        sub.current_period_start
                    ),
                    current_period_end=convert_tstamp(
                        sub.current_period_end
                    ),
                    amount=convert_amount_for_db(sub.plan.amount, sub.plan.currency),
                    currency=sub.plan.currency,
                    status=sub.status,
                    cancel_at_period_end=sub.cancel_at_period_end,
                    start=convert_tstamp(sub.start),
                    quantity=sub.quantity
                )

            if sub.trial_start and sub.trial_end:
                sub_obj.trial_start = convert_tstamp(sub.trial_start)
                sub_obj.trial_end = convert_tstamp(sub.trial_end)
                sub_obj.save()

            return sub_obj