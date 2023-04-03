from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from carts.models import CartItem
from store.forms import ReviewForm
from .models import Product, ReviewRating
from category.models import Category
from carts.views import _cart_id

# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None
    
    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.all().filter(category=categories, is_avaliable=True).order_by("id")
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_avaliable=True).order_by("id")
        product_count = products.count()
    
    paginator = Paginator(products, 3)
    page = request.GET.get("page")
    products_by_page = paginator.get_page(page)
    
    context = {
        "products": products_by_page,
        "product_count": product_count
    }
    return render(request, "store/store.html", context)

def product_detail(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
        
    except Exception as e:
        raise e
    
    context = {
        "product": product,
        "in_cart": in_cart
    }
    return render(request, "store/product_detail.html", context)


def search(request):
    products = None
    product_count = 0
    if "keyword" in request.GET:
        keyword = request.GET.get("keyword", "  ")
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(name__icontains=keyword))
            product_count = products.count()
    context = {
        "products": products,
        "product_count": product_count
    }
    return render(request, "store/store.html", context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        try: 
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id) 
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Thank you! Your review has been updated!")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id 
                messages.success(request, "Thank you! Your review has been submitted!")
                return redirect(url)