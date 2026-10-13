from django.http import Http404


class HideAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("__call__", request.user, request.user.is_superuser)
        print(
            request.path.startswith("/admin/")
            and (request.user.is_anonymous or not request.user.is_superuser)
        )
        print("request.user.is_authenticated", request.user.is_authenticated)
        print("not request.user.is_superuser", not request.user.is_superuser)

        if request.path.startswith("/admin/") and (
            request.user.is_anonymous or not request.user.is_superuser
        ):
            raise Http404
        print("before get_response")
        return self.get_response(request)
