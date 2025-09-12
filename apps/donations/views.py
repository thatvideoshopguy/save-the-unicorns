from django.shortcuts import render
from django.http import Http404
from apps.donations.forms import DonationForm


def donation_view(request):
    if not request.headers.get("HX-Request"):
        raise Http404("Page not found")

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save()
            return render(
                request,
                "donations/fragments/donate_success_fragment.html",
                {"donation": donation},
            )
        else:
            return render(
                request,
                "donations/fragments/donate_form_fragment.html",
                {"form": form},
            )

    form = DonationForm()
    return render(
        request,
        "donations/fragments/donate_form_fragment.html",
        {"form": form},
    )
