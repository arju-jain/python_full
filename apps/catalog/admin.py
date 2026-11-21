from django.contrib import admin
from .models import Category, Product, ProductImage
from apps.inventory.models import Inventory

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False
    verbose_name_plural = 'Inventory Stock'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'category', 'price', 'compare_at_price', 'sku', 'stock_quantity_display', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'category', 'vendor')
    search_fields = ('title', 'sku', 'description', 'vendor__store_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline, InventoryInline]

    @admin.display(description='Stock')
    def stock_quantity_display(self, obj):
        return obj.stock_quantity


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('is_primary',)
