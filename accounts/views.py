import json
import logging
import os
import re
import secrets

import django
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from app.views import validate_user_email
from .models import CustomUser

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

def get_logger():
    logger = logging.getLogger('views_account')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


log = get_logger()
username_pattern = re.compile('^[a-zA-Z0-9_.]+$')


def check_login(request):
    if request.method == 'POST':
        body = request.POST
        username = body['username'].lower()
        password = body['password']
        next_url = body['next']

        user = None
        if validate_user_email(username):
            user_set = CustomUser.objects.filter(email=username)

            if len(user_set) == 1:
                user = authenticate(username=user_set[0].username, password=password)
        else:
            user = authenticate(username=username, password=password)

        if user is None:
            log.info(f'{username} cannot be authenticated')
            return render(request, 'registration/login.html',
                          context={'username': username,
                                   'password': password,
                                   'error_login': 'Invalid credentials',
                                   'next': next_url})
        else:
            log.info(f'{username} has just logged in')
            django.contrib.auth.login(request, user)

            if next_url:
                return redirect(next_url)
            else:
                return redirect('index')


def check_regex(pattern, to_check):
    if pattern.match(to_check):
        return True
    else:
        return False


def check_existing_email(email):
    user_set = CustomUser.objects.filter(email=email, is_active=True)
    if len(user_set) > 0:
        return True
    else:
        return False


def send_confirmation_email(user):
    confirmation_email_text = f"""Hi {user.username},\n\nHere is the link to activate your DataTau account:\n\nhttps://datatau.net/accounts/login/activate/{user.id}/{user.api_key}\n\nWelcome to the coolest Data Science community!\n\nBR,\n\nDavid & Pedro"""
    send_mail(
        subject=f'Confirmation email from datatau.net',
        message=confirmation_email_text,
        from_email='info@datatau.net',
        recipient_list=[user.email],
        fail_silently=False
    )


def check_signup(request):
    if request.method == 'POST':
        body = request.POST
        username = body['username'].strip()
        password = body['password'].strip()
        email = body['email'].strip()
        next_url = body['next']

        if CustomUser.objects.filter(username=username).exists():
            log.info(f'username {username} already exists')
            return render(request, 'registration/login.html',
                          context={'error_signup': 'User already exists',
                                   'next': next_url})
        elif not password:
            log.info('empty password')
            return render(request, 'registration/login.html',
                          context={'error_signup': 'empty password',
                                   'next': next_url})
        elif not validate_user_email(email):
            log.info(f'not valid email: {email}')
            return render(request, 'registration/login.html',
                          context={'error_signup': f'not valid email: {email}',
                                   'next': next_url})
        elif check_existing_email(email):
            log.info(f'email {email} already exists')
            return render(request, 'registration/login.html',
                          context={'error_signup': f'email {email} already exists for a user, please try to login',
                                   'next': next_url})
        else:
            # Create the user and set their password
            user = CustomUser(username=username, email=email)
            user.set_password(password)
            user.is_active = True  # Set the user to active

            # Save the user
            user.save()
            log.info(f'{username} has just signed up and is now logged in.')

            # Log the user in immediately after registration
            login(request, user)

            # Redirect the user to the home page
            return redirect('index')  # 'index' should be the name of your homepage URL pattern


def activation(request, user_id, api_key):
    if request.method == 'GET':
        user_set = CustomUser.objects.filter(id=user_id)

        if len(user_set) == 1 and user_set[0].api_key == api_key:
            log.info(f'activating user {user_id}...')
            user = user_set[0]
            user.is_active = True
            user.save()

            django.contrib.auth.login(request, user)

        else:
            log.info(f'unable to activate user {user_id}')

        return redirect('index')


def reset_password(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()

        try:
            user = CustomUser.objects.get(username=username)
            # Generate a secure token and a uid
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Get the current site domain
            current_site = get_current_site(request)
            domain = current_site.domain

            # Create the reset link dynamically using the current site domain
            reset_link = f'http://{domain}/accounts/login/reset_password_confirm/{uid}/{token}/'

            # Create email content
            subject = "Password Reset Request"
            email_content = render_to_string('registration/reset_password_email.html',
                                             {'username': username, 'reset_link': reset_link})

            send_reset_email(user.email, subject, email_content)

            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('reset_password')
        except CustomUser.DoesNotExist:
            messages.error(request, 'This username does not exist.')
            return redirect('reset_password')

    return render(request, 'registration/reset_password.html')


def send_reset_email(email, subject, html_content):
    api_key = os.environ.get('BREVO_API_KEY')
    if not api_key:
        print("API key not found. Please set the 'BREVO_API_KEY' environment variable.")
        return

    api_url = 'https://api.brevo.com/v3/smtp/email'
    sender_email = 'stephenowabie@gmail.com'
    sender_name = 'Chistev'

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'api-key': api_key
    }

    response = requests.post(api_url, data=json.dumps(payload), headers=headers)

    if response.status_code == 201:
        print("Password reset email sent successfully.")
    else:
        print(f"Failed to send password reset email. Response: {response.text}")

def reset_password_confirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('login')  # Redirect to the login page

        return render(request, 'registration/reset_password_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('reset_password')


