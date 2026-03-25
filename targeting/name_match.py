"""Name normalization and matching between roster data and valuation/projection data.

Handles Unicode accents, Jr./Sr./II/III suffixes, and known manual aliases
for joining OnRoto roster names to FanGraphs-derived projection names.
"""

import unicodedata
import re

# Manual aliases: OnRoto roster name → FanGraphs/ATC projection name
# Only needed for names that can't be resolved by normalization alone
ROSTER_TO_PROJECTION = {
    "Bobby Witt": "Bobby Witt Jr.",
    "Lance McCullers": "Lance McCullers Jr.",
    "Mark Leiter": "Mark Leiter Jr.",
    "Luis M. Castillo": "Luis Castillo",
    "Mike King": "Michael King",
    "D.J. LeMahieu": "DJ LeMahieu",
    "Giovanny Urshela": "Gio Urshela",
    "Dee Gordon": "Dee Strange-Gordon",
    "Zach Britton": "Zack Britton",
    "Daniel Coulombe": "Danny Coulombe",
    "Enrique Hernandez": "Kiké Hernández",
    "Kike Hernandez": "Kiké Hernández",
    "Hyun Jin Ryu": "Hyun-Jin Ryu",
    "Cedric Mullins": "Cedric Mullins II",
    "Lourdes Gurriel": "Lourdes Gurriel Jr.",
    "Shohei Ohtani-Hitter": "Shohei Ohtani",
    "Nicholas Castellanos": "Nick Castellanos",
    "Nate Lowe": "Nathaniel Lowe",
}


def strip_accents(s: str) -> str:
    """Remove Unicode accents: Díaz → Diaz, Hernández → Hernandez."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_name(name: str) -> str:
    """Normalize a player name for fuzzy matching.

    Strips accents, removes Jr./Sr./II/III suffixes, lowercases,
    and removes punctuation. Used to build matching keys.
    """
    name = strip_accents(name.strip())
    # Remove suffixes
    name = re.sub(r"\s+(Jr\.?|Sr\.?|II|III|IV)\s*$", "", name)
    # Remove periods and hyphens, lowercase
    name = name.lower().replace(".", "").replace("-", " ")
    # Collapse whitespace
    name = " ".join(name.split())
    return name


def build_name_index(names: list[str]) -> dict[str, str]:
    """Build a normalized-name → original-name lookup dict.

    Args:
        names: List of original player names (e.g., from ATC projections).

    Returns:
        Dict mapping normalized keys to original names.
    """
    index = {}
    for name in names:
        key = normalize_name(name)
        if key not in index:
            index[key] = name
    return index


def match_name(roster_name: str, projection_index: dict[str, str]) -> str | None:
    """Match a roster name to a projection name.

    Tries in order:
    1. Manual alias lookup
    2. Normalized key matching (handles accents, suffixes, punctuation)

    Returns the projection-side name, or None if no match found.
    """
    # 1. Manual alias
    alias = ROSTER_TO_PROJECTION.get(roster_name)
    if alias:
        # Check if the alias actually exists in projections
        alias_key = normalize_name(alias)
        if alias_key in projection_index:
            return projection_index[alias_key]

    # 2. Normalized matching
    key = normalize_name(roster_name)
    if key in projection_index:
        return projection_index[key]

    return None
