from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy

User = get_user_model()


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'id', 'email', 'username', 'first_name',
        'last_name', 'is_staff', 'is_active'
    )

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (gettext_lazy('Personal info'),
         {'fields': ('first_name', 'last_name')}),
        (gettext_lazy('Permissions'),
         {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (gettext_lazy('Important dates'),
         {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_display_links = ('email',)
    ordering = ('email',)


admin.site.register(User, UserAdmin)
