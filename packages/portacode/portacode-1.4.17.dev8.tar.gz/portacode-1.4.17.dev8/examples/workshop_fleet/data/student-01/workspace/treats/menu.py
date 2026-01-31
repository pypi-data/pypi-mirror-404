"""
Static data backing the cupcake menu shown on the homepage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Cupcake:
    name: str
    flavor_notes: str
    price: str
    emoji: str = '🧁'
    is_limited: bool = False
    galaxy: str | None = None


CUPCAKES: list[Cupcake] = [
    Cupcake(
        name='Solar Flare',
        flavor_notes='orange zest + chili honey buttercream',
        price='5.50',
        emoji='🌞',
        galaxy='Mercury',
    ),
    Cupcake(
        name='Nebula Crunch',
        flavor_notes='blueberry jam, popping candy stardust',
        price='4.75',
        emoji='✨',
        galaxy='NGC 6357',
    ),
    Cupcake(
        name='Lunar Latte',
        flavor_notes='espresso sponge with caramel moon drizzle',
        price='5.00',
        emoji='🌙',
        galaxy="Earth's Moon",
    ),
    Cupcake(
        name='Comet Confetti',
        flavor_notes='vanilla bean base + rainbow meteor sprinkles',
        price='4.25',
        emoji='☄️',
        galaxy='Kuiper Belt',
    ),
    Cupcake(
        name='Aurora Velvet',
        flavor_notes='red velvet nebula with pistachio aurora frosting',
        price='6.25',
        emoji='🌌',
        is_limited=True,
        galaxy='Andromeda',
    ),
    Cupcake(
        name="Gravity S'mores",
        flavor_notes='toasted marshmallow mousse, graham soil, dark matter ganache',
        price='5.95',
        emoji='🛰️',
        galaxy='Milky Way',
    ),
]


def limited_time_specials() -> list[Cupcake]:
    """Return the cupcakes that are only around for a short orbit."""
    return [cupcake for cupcake in CUPCAKES if cupcake.is_limited]
