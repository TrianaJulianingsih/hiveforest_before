from django.shortcuts import render
from django.contrib.auth.views import LoginView

# START - FaisalS | Fixed Redirect & Cache
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# END - FaisalS | Fixed Redirect & Cache


# Create your views here.
def pandas_import(request):
    return render(request, "admin/pandas_import.html")


# START - FaisalS | Fixed Redirect & Cache
@method_decorator(never_cache, name="dispatch")
class CustomAdminLoginView(LoginView):
    template_name = "auth/login.html"
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            return render(request, "404.html", status=404)
        return super().dispatch(request, *args, **kwargs)
# END - FaisalS | Fixed Redirect & Cache


def custom_404(request, exception=None):
    return render(request, "404.html", {"message": "Page Not Found"}, status=404)
