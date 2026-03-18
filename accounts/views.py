from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views import View
from .models import User, Emailcode
from .utilis import send_email_code


# Create your views here.


class RegisterView(View):

    def get(self, request):
        return render(request, 'accounts/register.html')

    def post(self, request):
        full_name = request.POST.get('full_name')
        email     = request.POST.get('email')
        password  = request.POST.get('password')
        role      = request.POST.get('role')

        if not full_name or not email or not password or not role:
            return render(request, 'accounts/register.html', {
                'error': 'Barcha maydonlarni to\'ldiring'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/register.html', {
                'error': 'Bu email allaqachon ro\'yxatdan o\'tgan'
            })

        user = User.objects.create_user(
            username  = email,
            email     = email,
            password  = password,
            full_name = full_name,
            role      = role,
            is_active = False,
        )

        send_email_code(user)
        request.session['pending_email'] = email
        return redirect('accounts:verify_email')


class VerifyEmailView(View):

    def get(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')
        return render(request, 'accounts/verify_email.html', {'email': email})

    def post(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')

        code = request.POST.get('code')

        try:
            user       = User.objects.get(email=email)
            email_code = Emailcode.objects.filter(
                user         = user,
                code         = code,
                is_activated = False
            ).last()

            if not email_code:
                return render(request, 'accounts/verify_email.html', {
                    'error': 'Kod noto\'g\'ri'
                })

            if email_code.is_expired():
                return render(request, 'accounts/verify_email.html', {
                    'error': 'Kod muddati o\'tgan. Qayta yuboring.'
                })

            email_code.is_activated = True
            email_code.save(update_fields=['is_activated'])

            user.is_active = True
            user.save(update_fields=['is_active'])

            del request.session['pending_email']

            login(request, user)
            return redirect('marketplace:order_list')

        except User.DoesNotExist:
            return redirect('accounts:register')


class ResendCodeView(View):

    def get(self, request):
        email = request.session.get('pending_email')
        if not email:
            return redirect('accounts:register')

        try:
            user = User.objects.get(email=email)
            send_email_code(user)
        except User.DoesNotExist:
            return redirect('accounts:register')

        return redirect('accounts:verify_email')