from django.shortcuts import render, get_object_or_404
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from carts.models import CartItem
from .models import Product
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