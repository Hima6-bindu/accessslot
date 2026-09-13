"""
Django admin configuration for Equipment, Booking, UsageLimit, Maintenance, and WaitingList models.
"""
from django.contrib import admin
from .models import Equipment, Booking, UsageLimit, Maintenance, WaitingList


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Equipment model.
    """
    list_display = [
        'name',
        'equipment_type',
        'location',
        'status',
        'max_booking_duration',
        'created_at'
    ]
    list_filter = [
        'status',
        'equipment_type',
        'location',
        'created_at'
    ]
    search_fields = [
        'name',
        'description',
        'equipment_type',
        'location'
    ]
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'description',
                'equipment_type',
                'location'
            )
        }),
        ('Status & Configuration', {
            'fields': (
                'status',
                'max_booking_duration'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queryset for list display.
        """
        qs = super().get_queryset(request)
        return qs.select_related()
    
    # Enable actions for bulk operations
    actions = ['mark_as_available', 'mark_as_maintenance', 'mark_as_disabled']
    
    @admin.action(description='Mark selected equipment as Available')
    def mark_as_available(self, request, queryset):
        """Bulk action to mark equipment as available."""
        updated = queryset.update(status=Equipment.Status.AVAILABLE)
        self.message_user(request, f'{updated} equipment marked as Available.')
    
    @admin.action(description='Mark selected equipment as Under Maintenance')
    def mark_as_maintenance(self, request, queryset):
        """Bulk action to mark equipment as under maintenance."""
        updated = queryset.update(status=Equipment.Status.MAINTENANCE)
        self.message_user(request, f'{updated} equipment marked as Under Maintenance.')
    
    @admin.action(description='Mark selected equipment as Disabled')
    def mark_as_disabled(self, request, queryset):
        """Bulk action to mark equipment as disabled."""
        updated = queryset.update(status=Equipment.Status.DISABLED)
        self.message_user(request, f'{updated} equipment marked as Disabled.')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin interface for Booking model.
    """
    list_display = [
        'id',
        'user',
        'equipment',
        'start_time',
        'end_time',
        'status',
        'duration_display',
        'created_at'
    ]
    list_filter = [
        'status',
        'equipment',
        'start_time',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'equipment__name',
        'cancellation_reason'
    ]
    ordering = ['-start_time']
    readonly_fields = ['created_at', 'updated_at', 'duration_display']
    
    fieldsets = (
        ('Booking Information', {
            'fields': (
                'user',
                'equipment',
                'start_time',
                'end_time',
                'duration_display'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'cancellation_reason'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queryset for list display.
        """
        qs = super().get_queryset(request)
        return qs.select_related('user', 'equipment')
    
    def duration_display(self, obj):
        """Display booking duration in hours."""
        return f"{obj.duration_hours:.1f} hours"
    duration_display.short_description = 'Duration'
    
    # Bulk actions
    actions = ['mark_as_completed', 'mark_as_no_show']
    
    @admin.action(description='Mark selected bookings as Completed')
    def mark_as_completed(self, request, queryset):
        """Bulk action to mark bookings as completed."""
        updated = queryset.update(status=Booking.Status.COMPLETED)
        self.message_user(request, f'{updated} bookings marked as Completed.')
    
    @admin.action(description='Mark selected bookings as No Show')
    def mark_as_no_show(self, request, queryset):
        """Bulk action to mark bookings as no show."""
        updated = queryset.update(status=Booking.Status.NO_SHOW)
        self.message_user(request, f'{updated} bookings marked as No Show.')


@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    """
    Admin interface for UsageLimit model.
    """
    list_display = [
        'role',
        'max_weekly_hours'
    ]
    search_fields = ['role']
    ordering = ['role']
    
    fieldsets = (
        ('Usage Limit Configuration', {
            'fields': (
                'role',
                'max_weekly_hours'
            )
        }),
    )


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    """
    Admin interface for Maintenance model.
    """
    list_display = [
        'id',
        'equipment',
        'start_time',
        'end_time',
        'reason_short',
        'created_by',
        'created_at'
    ]
    list_filter = [
        'equipment',
        'start_time',
        'created_at'
    ]
    search_fields = [
        'equipment__name',
        'reason',
        'created_by__username'
    ]
    ordering = ['-start_time']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Maintenance Information', {
            'fields': (
                'equipment',
                'start_time',
                'end_time',
                'reason'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queryset for list display.
        """
        qs = super().get_queryset(request)
        return qs.select_related('equipment', 'created_by')
    
    def reason_short(self, obj):
        """Display shortened reason."""
        if len(obj.reason) > 50:
            return f"{obj.reason[:50]}..."
        return obj.reason
    reason_short.short_description = 'Reason'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating."""
        if not change:  # Creating new
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    """
    Admin interface for WaitingList model.
    """
    list_display = [
        'id',
        'user',
        'equipment',
        'position',
        'status',
        'requested_start_time',
        'requested_end_time',
        'created_at'
    ]
    list_filter = [
        'status',
        'equipment',
        'created_at'
    ]
    search_fields = [
        'user__username',
        'user__email',
        'equipment__name'
    ]
    ordering = ['equipment', 'position', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'position']
    
    fieldsets = (
        ('Waiting List Entry', {
            'fields': (
                'user',
                'equipment',
                'requested_start_time',
                'requested_end_time',
                'position',
                'status'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """
        Optimize queryset for list display.
        """
        qs = super().get_queryset(request)
        return qs.select_related('user', 'equipment')
    
    # Bulk actions
    actions = ['mark_as_notified', 'mark_as_cancelled', 'mark_as_fulfilled']
    
    @admin.action(description='Mark selected entries as Notified')
    def mark_as_notified(self, request, queryset):
        """Bulk action to mark entries as notified."""
        updated = queryset.update(status=WaitingList.Status.NOTIFIED)
        self.message_user(request, f'{updated} entries marked as Notified.')
    
    @admin.action(description='Mark selected entries as Cancelled')
    def mark_as_cancelled(self, request, queryset):
        """Bulk action to mark entries as cancelled."""
        updated = queryset.update(status=WaitingList.Status.CANCELLED)
        self.message_user(request, f'{updated} entries marked as Cancelled.')
    
    @admin.action(description='Mark selected entries as Fulfilled')
    def mark_as_fulfilled(self, request, queryset):
        """Bulk action to mark entries as fulfilled."""
        updated = queryset.update(status=WaitingList.Status.FULFILLED)
        self.message_user(request, f'{updated} entries marked as Fulfilled.')
