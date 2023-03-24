from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.contrib import messages, auth
from accounts.models import Account
from django.contrib.auth.decorators import login_required

import requests

# Email verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings


from .forms import RegistrationForm
from carts.views import _cart_id
from carts.models import Cart, CartItem
# Create your views here.

def send_verify_email(user, request):
    #  user activation
    current_site = get_current_site(request)
    mail_subject = "Please activate your account"
    email_body = render_to_string("accounts/account_verification_email.html", {
        "user": user,
        "domain": current_site,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
    })
    
    send_email = EmailMessage(subject=mail_subject, body=email_body, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email])
    send_email.send()
    
    
def send_reset_password(user, request):
    # Reset password email
    current_site = get_current_site(request)
    mail_subject = "Reset your password"
    email_body = render_to_string("accounts/reset_password_email.html", {
        "user": user,
        "domain": current_site,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
    })
    
    send_email = EmailMessage(subject=mail_subject, body=email_body, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email])
    send_email.send()
            
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]
            phone_number = form.cleaned_data["phone_number"]
            password = form.cleaned_data["password"]
            username = email.split("@")[0]
            
            user = Account.objects.create_user(first_name=first_name, last_name=last_name,
                                email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()
            
            send_verify_email(user, request)
            
            messages.success(request, "Thank you for registration. We have sent a verification email to your email address. Please verify it!")
            
            return redirect(f"/accounts/login/?command=verification&email={email}")
    else:
        form = RegistrationForm()
        
    context = {
        "form": form
    }
    
    return render(request, "accounts/register.html", context)

def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        
        user = auth.authenticate(email=email, password=password)
        if user is not None:
            # if user is not authorizated and has some items in cart, bring them with him
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # getting the product variations by cart id
                    product_variations = []
                    for item in cart_item:
                        varitation = item.variations.all()
                        product_variations.append(list(varitation)) # by default is a query list
                        
                    # get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    existing_variations_list, ids = [], []
        
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        existing_variations_list.append(list(existing_variation))
                        ids.append(item.id)
                        
                    for product in product_variations:
                        if product in existing_variations_list:
                            index = existing_variations_list.index(product)
                            item = CartItem.objects.get(id=ids[index])
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass 
            auth.login(request, user)
            messages.success(request, "You are now logged in!")
            # redirect to checkout page when user is logged in by using checkout button
            url = request.META.get('HTTP_REFERER')
            try:
                # next=/cart/checkout
                query = requests.utils.urlparse(url).query # get path after ?
                params = dict(x.split("=") for x in query.split("&"))
                if "next" in params:
                    next_page = params["next"]
                    return redirect(next_page)
            except:
                return redirect("dashboard")
        else:
            messages.success(request, "Invalid login credentials or your account is not activated!")
            return redirect("login")
    return render(request, "accounts/login.html")


@login_required(login_url = "login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out!")
    return redirect("login")


def activate_user(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations! Your account is activated! Now you can login up)")
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link")
        return redirect("register")
    
    
@login_required  
def dashboard(request):
    return render(request, "accounts/dashboard.html")


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)
            
            send_reset_password(user, request)
            
            messages.success(request, "Password reset email has been sent to your email address!")
            return redirect("login")
        else:
            messages.error(request, "Account doesn't exists!")
            return redirect("forgotPassword")
        
    return render(request, "accounts/forgotPassword.html")


def resetPassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please, enter the new password")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("login")


def resetPassword(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        
        if password == confirm_password:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            
            messages.success(request, "Password changed successully!")
            return redirect("login")
        else:
            messages.error(request, "Passwords do not match!")
            return redirect("resetPassword")
    else:
        return render(request, "accounts/resetPassword.html")