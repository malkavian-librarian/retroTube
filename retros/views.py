from django.shortcuts import get_object_or_404, redirect, render

from retros.forms import CreateRetroForm
from retros.models import Retro
from retros.services import create_retro


def create_retro_view(request):
    if request.method == "POST":
        form = CreateRetroForm(request.POST)
        if form.is_valid():
            retro = create_retro(
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                participant_limit=form.cleaned_data["participant_limit"],
                raw_pin=form.cleaned_data["pin"],
            )
            return redirect("retro_detail", pk=retro.pk)
    else:
        form = CreateRetroForm()

    return render(request, "retros/create_retro.html", {"form": form})


def retro_detail_view(request, pk):
    retro = get_object_or_404(Retro, pk=pk)
    return render(request, "retros/retro_detail.html", {"retro": retro})
