import inspect

from sanic import Blueprint

from srf.views.base import BaseViewSet


class SanicRouter:
    def __init__(self, bp: Blueprint = None, prefix: str = ""):
        self.prefix = f"/{prefix.strip('/')}" if prefix else ""
        self.bp = bp or Blueprint(self.prefix.strip("/") or "api")

    def register(self, path: str, view_cls: BaseViewSet, name: str = None):
        name = name or path
        path = path.strip("/")
        base_uri = f"{self.prefix}/{path}"

        # register list/create（without id）
        self.bp.add_route(
            view_cls.as_view(actions={"get": "list", "post": "create"}),
            base_uri,
            methods=["GET", "POST"],
            name=f"{name}-list",
        )

        # register retrieve/update/destroy（with id/pk）
        detail_uri = f"{base_uri}/<pk:int>"
        self.bp.add_route(
            view_cls.as_view(
                actions={
                    "get": "retrieve",
                    "put": "update",
                    "patch": "update",
                    "delete": "destroy",
                }
            ),
            detail_uri,
            methods=["GET", "PUT", "PATCH", "DELETE"],
            name=f"{name}-detail",
        )

        # decorator route
        for method_name, func in inspect.getmembers(view_cls, predicate=inspect.isfunction):
            if extra_info := getattr(func, "extra_info", None):
                # Create a closure to capture the method name correctly
                def make_route_view(action_name):
                    async def route_view(request, *args, **kwargs):
                        """
                        Route view for custom action methods.
                        Creates a new view instance for each request to ensure proper state isolation.
                        """
                        view_instance = view_cls()
                        view_instance.request = request

                        # Check permissions if permission_classes are defined
                        # FIXME The way of binding the router between the decorator function and the class function is different, which results in that the decorator function cannot use many properties of the class, so the interface permission verification written here temporarily
                        if hasattr(view_cls, "permission_classes") and view_cls.permission_classes:
                            await view_instance.check_permissions(request)

                        # Get and call the action method
                        action_method = getattr(view_instance, action_name)
                        return await action_method(request, *args, **kwargs)

                    return route_view

                route_view = make_route_view(method_name)

                if not extra_info.get("detail"):
                    uri = "/".join([self.prefix.lstrip("/"), path.rstrip("/"), extra_info["url_path"].lstrip("/")])
                else:
                    uri = "/".join([self.prefix.lstrip("/"), path.rstrip("/"), "<pk:int>", extra_info["url_path"].lstrip("/")])
                self.bp.add_route(
                    route_view,
                    methods=extra_info["methods"],
                    uri=uri,
                    name=extra_info["url_name"],
                )

    def get_blueprint(self):
        return self.bp
