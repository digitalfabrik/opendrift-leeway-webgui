from django.contrib import admin
from django.utils.html import format_html

from .models import InvitationToken, LeewaySimulation

admin.site.register(LeewaySimulation)


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for managing invitation tokens.
    Tokens are auto-generated and immutable once created.
    """

    #: Columns shown in the changelist
    list_display = (
        "token",
        "created_at",
        "is_used",
        "used_by",
        "copy_registration_link",
    )

    #: Fields the admin can never edit
    readonly_fields = ("token", "created_at", "used_by")

    def has_change_permission(self, request, obj=None):
        """
        Tokens are immutable — disallow editing after creation.
        """
        return False

    @admin.display(description="Registration link")
    def copy_registration_link(self, obj):
        """
        Render a clipboard button for unused tokens, empty for used ones.
        """
        if obj.is_used:
            return ""
        path = f"/accounts/register/{obj.token}/"
        return format_html(
            '<button type="button" '
            "onclick=\"navigator.clipboard.writeText(window.location.origin + '{}');\">"
            "Copy link"
            "</button>",
            path,
        )
