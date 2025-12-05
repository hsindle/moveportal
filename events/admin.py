# events/admin.py

from django.contrib import admin
from .models import Event, EventArtwork, EventCategory, Promoter # Ensure ALL models are imported

# Inline form for managing artwork directly on the Event detail page
class EventArtworkInline(admin.TabularInline):
    model = EventArtwork
    extra = 1

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # 🚨 FIX 1: Update list_display to use ForeignKey lookups 🚨
    list_display = (
        'name', 
        'start_date', 
        'get_category_name',  # Custom method to display Category Name
        'get_promoter_name',  # Custom method to display Promoter Name
        'is_active'
    )
    
    # 🚨 FIX 2: Update list_filter to use ForeignKey lookup paths 🚨
    list_filter = ('category', 'is_active', 'start_date')
    
    search_fields = ('name', 'promoter__name', 'notes')
    date_hierarchy = 'start_date'
    
    # Add the artwork inline to the main Event form
    inlines = [EventArtworkInline]
    
    # Custom Methods to safely display ForeignKey names in list_display
    def get_category_name(self, obj):
        return obj.category.name if obj.category else 'N/A'
    get_category_name.short_description = 'Event Type'

    def get_promoter_name(self, obj):
        return obj.promoter.name if obj.promoter else 'N/A'
    get_promoter_name.short_description = 'Promoter'


    # Customize the fields shown on the detail page (Verify these fields are correct)
    fieldsets = (
        (None, {
            # FIX 3: Use the new FK fields 
            'fields': ('name', 'category', 'promoter', 'is_active', 'team'),
        }),
        ('Schedule and Logistics', {
            'fields': ('start_date', 'end_date', 'notes'),
        }),
        ('Riders and Files', {
            'fields': ('epk_link', 'hospitality_rider', 'technical_rider'),
        }),
    )

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code')
    
@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')

@admin.register(EventArtwork)
class EventArtworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'event')