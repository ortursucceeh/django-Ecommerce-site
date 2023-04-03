import django.contrib.auth.admin
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

from store.models import Product, Variation
from .models import Cart, CartItem

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    
    if not cart:
        cart = request.session.create()
            
    return cart
     
def add_variations_to_item(item, product_variations):
    if len(product_variations) > 0:
        item.variations.clear()
        item.variations.add(*product_variations)
        
def add_existing_variations(cart_item, product, product_variations, is_authenticated=False, current_user=None):
        existing_variations_list, ids = [], []
        
        for item in cart_item:
            existing_variation = item.variations.all()
            existing_variations_list.append(list(existing_variation))
            ids.append(item.id)
            
        if product_variations in existing_variations_list:
            index = existing_variations_list.index(product_variations) 
            item = CartItem.objects.get(product=product, id=ids[index])
            item.quantity += 1
            item.save()
        else:
            if not is_authenticated:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                
            
            # adding the chosen variations to cart_item
            add_variations_to_item(item, product_variations)
                
            item.save()
            
def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    # if user authenticated
    if current_user.is_authenticated:
        product_variations = []
        
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST.get(key)
                
                try:
                    variation = Variation.objects.get(product=product, category__iexact=key, value__iexact=value) #  __iexact - igonres the letter casing
                    product_variations.append(variation)
                except:
                    pass
        
        
        #  existing variations
        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            add_existing_variations(cart_item, product, product_variations, is_authenticated=True, current_user=current_user)
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user, 
            )
            # adding the chosen variations to cart_item
            add_variations_to_item(cart_item, product_variations)
                    
            cart_item.save()
            
        return redirect('cart')
    # if user is not authenticated
    else:
        product_variations = []
        
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST.get(key)
                
                try:
                    variation = Variation.objects.get(product=product, category__iexact=key, value__iexact=value) #  __iexact - igonres the letter casing
                    product_variations.append(variation)
                except:
                    pass
            
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) 
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
        
        
        #  existing variations
        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            
            add_existing_variations(cart_item, product, product_variations)

            
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart, 
            )
            # adding the chosen variations to cart_item
            add_variations_to_item(cart_item, product_variations)
                    
            cart_item.save()
            
        return redirect('cart')
    
def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
        
    return redirect('cart')
    
def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect("cart")
    
    
    
def cart(request, total=0, quantity=0, cart_items=0):
    try:
        tax, grand_total = 0, 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
        
    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total
    }
    
    return render(request, "store/cart.html", context)

@login_required(login_url="login")
def checkout(request, total=0, quantity=0, cart_items=[]):
    try:
        tax, grand_total = 0, 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass
        
    context = {
        "total": total,
        "quantity": quantity,
        "cart_items": cart_items,
        "tax": tax,
        "grand_total": grand_total
    }
    
    return render(request, "store/checkout.html", context)