from __future__ import annotations

import random
from datetime import datetime
from decimal import Decimal

from django.shortcuts import render

from .menu import CUPCAKES, limited_time_specials


def _cheapest_cupcake():
    return min(CUPCAKES, key=lambda cupcake: Decimal(cupcake.price))


def home(request):
    """Render the cupcake menu, prioritizing any limited specials."""
    specials = limited_time_specials()
    featured_pool = specials or CUPCAKES
    featured = random.choice(featured_pool)
    context = {
        "featured": featured,
        "cupcakes": CUPCAKES,
        "limited_specials": specials,
        "cheapest": _cheapest_cupcake(),
        "generated_at": datetime.utcnow(),
    }
    return render(request, "treats/home.html", context)
