from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate,login,logout


from .models import User, Emailcode
from .utilis import send_email_code


class RegisterView(View):
    """Yangi foydalanuvchini ro'yxatdan o'tkazish."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('marketplace:order_list')
        return render(request, 'accounts/register.html')

    def post(self, request):
        full_name = request.POST.get('full_name', '').strip()
        email     = request.POST.get('email', '').strip().lower()
        password  = request.POST.get('password', '')
        role      = request.POST.get('role', '')

        # --- Maydon tekshiruvi ---
        if not all([full_name, email, password, role]):
            return render(request, 'accounts/register.html', {
                'error': 'Barcha maydonlarni to\'ldiring',
                'full_name': full_name,
                'email': email,
                'role': role,
            })

        if role not in ('CLIENT', 'FREELANCER'):
            return render(request, 'accounts/register.html', {
                'error': 'Noto\'g\'ri rol tanlandi',
            })

        if len(password) < 8:
            return render(request, 'accounts/register.html', {
                'error': 'Parol kamida 8 ta belgidan iborat bo\'lishi kerak',
                'full_name': full_name,
                'email': email,
                'role': role,
            })

        # --- Timing attack'dan himoya: mavjud bo'lsa ham xuddi shu javob ---
        user_exists = User.objects.filter(email=email).exists()

        if not user_exists:
            user = User.objects.create_user(
                username  = email,
                email     = email,
                password  = password,
                full_name = full_name,
                role      = role,
                is_active = False,
            )
            send_email_code(user)

        # Mavjud bo'lsa ham xuddi shu sahifaga yo'naltiramiz
        request.session['pending_email'] = email
        return redirect('accounts:verify_email')


class VerifyEmailView(View):
    """Email tasdiqlash kodi tekshiruvi."""

    def get(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')
        return render(request, 'accounts/verify_email.html', {'email': email})

    @method_decorator(ratelimit(key='ip', rate='5/10m', method='POST', block=True))
    def post(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')

        code = request.POST.get('code', '').strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return redirect('accounts:register')

        email_code = Emailcode.objects.filter(
            user         = user,
            code         = code,
            is_activated = False,
        ).last()

        if not email_code:
            return render(request, 'accounts/verify_email.html', {
                'email': email,
                'error': 'Kod noto\'g\'ri',
            })

        if email_code.is_expired():
            email_code.delete()  # Muddati o'tgan kodni tozalash
            return render(request, 'accounts/verify_email.html', {
                'email': email,
                'error': 'Kod muddati o\'tgan. Qayta yuboring.',
            })

        # Kodni faollashtirish
        email_code.is_activated = True
        email_code.save(update_fields=['is_activated'])

        # Foydalanuvchini faollashtirish
        user.is_active = True
        user.save(update_fields=['is_active'])

        # Sessiyani tozalash
        del request.session['pending_email']

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('marketplace:order_list')


class ResendCodeView(View):
    """Tasdiqlash kodini qayta yuborish."""

    @method_decorator(ratelimit(key='ip', rate='3/10m', method='GET', block=True))
    def get(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')

        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return redirect('accounts:register')

        # Eski muddati o'tgan kodlarni tozalash
        Emailcode.objects.filter(user=user, is_activated=False).delete()

        send_email_code(user)
        return redirect('accounts:verify_email')



class LoginView(View):
    """Foydalanuvchi tizimga kirishi."""

    def get(self, request):
        # Agar foydalanuvchi allaqachon kirgan bo'lsa, asosiy sahifaga yuboramiz
        if request.user.is_authenticated:
            return redirect('marketplace:order_list')
        return render(request, 'accounts/login.html')

    @method_decorator(ratelimit(key='ip', rate='5/5m', method='POST', block=True))
    def post(self, request):
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            return render(request, 'accounts/login.html', {
                'error': 'Email va parolni kiriting',
                'email': email
            })

        # User modelida USERNAME_FIELD = 'email' bo'lgani uchun
        # authenticate() funksiyasi email va password qabul qiladi
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                # Foydalanuvchi qayerdan kelgan bo'lsa o'sha yerga (next),
                # bo'lmasa marketplace'ga yuboramiz
                next_url = request.GET.get('next', 'marketplace:order_list')
                return redirect(next_url)
            else:
                # Agar profil faol bo'lmasa (email tasdiqlanmagan bo'lsa)
                request.session['pending_email'] = email
                return render(request, 'accounts/login.html', {
                    'error': 'Hisobingiz faol emas. Iltimos, emailni tasdiqlang.',
                    'email': email,
                    'is_not_active': True # Template'da tasdiqlash tugmasini chiqarish uchun
                })
        else:
            return render(request, 'accounts/login.html', {
                'error': 'Email yoki parol noto\'g\'ri',
                'email': email
            })

def logout_out(request):
    logout(request)
    return redirect('marketplace:order_list')