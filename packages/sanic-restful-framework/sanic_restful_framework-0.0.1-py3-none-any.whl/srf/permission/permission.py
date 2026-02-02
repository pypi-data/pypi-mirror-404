class BasePermission(metaclass=type):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class IsRoleAdminUser(BasePermission):
    def has_permission(self, request, view=None):
        return request.ctx.user is not None and bool(request.ctx.user.role.name == "admin")


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view=None):
        return request.ctx.user is not None and bool(request.ctx.user.is_active)
