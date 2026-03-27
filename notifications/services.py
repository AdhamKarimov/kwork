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


def notify_offer_received(client, freelancer_name, order_title, order_pk, room_pk=None):
    """Mijozga: frilanser taklif yubordi — chatga o'tish linki."""
    if room_pk:
        link = reverse('chat:room_detail', kwargs={'room_id': room_pk})
    else:
        link = reverse('marketplace:order_detail', kwargs={'pk': order_pk})

    Notification.objects.create(
        user    = client,
        type    = Notification.Type.OFFER_RECEIVED,
        message = f'📩 {freelancer_name} "{order_title}" buyurtmangizga taklif yubordi.',
        link    = link,
    )


def notify_offer_accepted(freelancer, order_title, order_pk, room_pk=None):
    """Frilansерga: taklif qabul qilindi — chatga o'tish linki."""
    if room_pk:
        link = reverse('chat:room_detail', kwargs={'room_id': room_pk})
    else:
        link = reverse('marketplace:order_detail', kwargs={'pk': order_pk})

    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.OFFER_ACCEPTED,
        message = f'✅ Taklifingiz qabul qilindi! "{order_title}" loyihasi boshlandi.',
        link    = link,
    )


def notify_offer_rejected(freelancer, order_title, order_pk, room_pk=None):
    """Frilansерga: taklif rad etildi — chatga o'tish linki."""
    if room_pk:
        link = reverse('chat:room_detail', kwargs={'room_id': room_pk})
    else:
        link = reverse('marketplace:order_detail', kwargs={'pk': order_pk})

    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.OFFER_REJECTED,
        message = f'❌ "{order_title}" buyurtmasi uchun taklifingiz rad etildi.',
        link    = link,
    )


def notify_work_submitted(client, freelancer_name, order_title, order_pk, room_pk):
    """Mijozga: frilanser ish topshirdi."""
    Notification.objects.create(
        user    = client,
        type    = Notification.Type.OFFER_RECEIVED,
        message = f'📦 {freelancer_name} "{order_title}" loyihasi bo\'yicha ish topshirdi.',
        link    = reverse('chat:room_detail', kwargs={'room_id': room_pk}),
    )


def notify_work_approved(freelancer, order_title, order_pk, rating):
    """Frilansерga: ish tasdiqlandi + baho."""
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.ORDER_COMPLETED,
        message = f'🎉 "{order_title}" loyihasi tasdiqlandi! Baho: {"⭐" * rating}',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )


def notify_work_rejected(freelancer, order_title, order_pk):
    """Frilansерga: ish qayta ishlash kerak."""
    Notification.objects.create(
        user    = freelancer,
        type    = Notification.Type.DEADLINE_SOON,
        message = f'🔄 "{order_title}" loyihasi bo\'yicha qayta ishlash so\'raldi.',
        link    = reverse('marketplace:order_detail', kwargs={'pk': order_pk}),
    )