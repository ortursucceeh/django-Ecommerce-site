from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery
import admin_thumbnails

# Register your models here.

@admin_thumbnails.thumbnail("image")
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    
    
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "category", "modified_date")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductGalleryInline]
    
    
class VariationAdmin(admin.ModelAdmin):
    list_display = ("product", "category", "value", "is_active")
    list_editable = ("is_active",)
    list_filter = ("product", "category", "value")
    
        
admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(ReviewRating)
admin.site.register(ProductGallery)
