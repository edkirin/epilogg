from django.http import HttpResponseRedirect
from django.contrib import auth
from django.shortcuts import render


#--------------------------------------------------------------------------------------------------


def login(request):
    from django.contrib import auth
    from project.main.util import get_ip_from_request

    if request.user.is_authenticated and request.user.is_active:
        return HttpResponseRedirect('/')

    next = request.GET.get("next", "")
    err = False

    if request.method == "POST":
        ident = request.POST.get("ident")
        password = request.POST.get("password")
        next = request.POST.get("next", "")

        user = auth.authenticate(username=ident, password=password)
        if user is None:
            user = auth.authenticate(email=ident, password=password)
        if user is not None:
            auth.login(request, user)

        if user is not None:
            return HttpResponseRedirect(next)
        else:
            err = True

    return render(request, "registration/login.html",
        {
            "next": next,
            "err": err,
            "ip_address": get_ip_from_request(request),
        }
    )


#--------------------------------------------------------------------------------------------------
