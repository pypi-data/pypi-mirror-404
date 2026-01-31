"""Random Docker-style agent name generator.

Generates names like "bold-turing", "swift-hopper", etc.
"""

import random

ADJECTIVES = [
    "bold",
    "bright",
    "calm",
    "clever",
    "crisp",
    "deft",
    "eager",
    "fast",
    "firm",
    "glad",
    "keen",
    "lucid",
    "neat",
    "noble",
    "prime",
    "quick",
    "sharp",
    "sleek",
    "smart",
    "solid",
    "steady",
    "strong",
    "subtle",
    "sure",
    "swift",
    "tidy",
    "vivid",
    "warm",
    "wise",
    "witty",
]

SURNAMES = [
    "babbage",
    "bell",
    "boole",
    "cerf",
    "church",
    "conway",
    "curie",
    "darwin",
    "dijkstra",
    "euler",
    "faraday",
    "feynman",
    "gauss",
    "hopper",
    "johnson",
    "kahn",
    "knuth",
    "lamarr",
    "leibniz",
    "lovelace",
    "maxwell",
    "neumann",
    "noether",
    "pascal",
    "planck",
    "ritchie",
    "shannon",
    "tesla",
    "thompson",
    "turing",
]

_rng = random.SystemRandom()


def generate_agent_name() -> str:
    """Return a random Docker-style name, e.g. 'bold-turing'."""
    return f"{_rng.choice(ADJECTIVES)}-{_rng.choice(SURNAMES)}"
