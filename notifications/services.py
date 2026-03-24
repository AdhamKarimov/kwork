from .models import Notification
from django.urls import reverse


def notify_deadline_soon(freelancer, order_title, order_pk):
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.DEADLINE_SOON,
        message = f'"{order_title}" loyihasining muddati 1 soatdan kam qoldi!',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_deadline_passed(freelancer, order_title, order_pk):
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.DEADLINE_PASSED,
        message = f'"{order_title}" loyihasining muddati o\'tib ketdi.',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_order_completed(freelancer, order_title, order_pk):
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.ORDER_COMPLETED,
        message = f'"{order_title}" loyihasi mijoz tomonidan yakunlandi!',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_offer_received(client, freelancer_name, order_title, order_pk):
    Notification.objects.create(
        user    = client,
        type    = Notification.Type.OFFER_RECEIVED,
        message = f'{freelancer_name} "{order_title}" buyurtmangizga murojaat qildi.',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_offer_accepted(freelancer, order_title, order_pk):
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.OFFER_ACCEPTED,
        message = f'Taklifingiz qabul qilindi! "{order_title}" loyihasi boshlandi.',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_offer_rejected(freelancer, order_title, order_pk):
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.OFFER_REJECTED,
        message = f'"{order_title}" buyurtmasi uchun taklifingiz rad etildi.',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )