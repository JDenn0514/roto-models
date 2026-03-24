"""League constants and model configuration for SGP calibration."""

from dataclasses import dataclass, field, replace


@dataclass
class CategorySettings:
    """Per-category model settings for composite configs."""

    sgp_method: str
    use_supplemental: bool
    time_decay: bool
    time_decay_rate: float
    punt_detection: bool


# Sweep-derived composite winners (2026-03-24 sweep, 320 configs, 6 primary years incl 2025)
COMPOSITE_DEFAULTS: dict[str, CategorySettings] = {
    "R":    CategorySettings("ols",             use_supplemental=False, time_decay=True,  time_decay_rate=0.80, punt_detection=False),
    "HR":   CategorySettings("pairwise_mean",   use_supplemental=True,  time_decay=False, time_decay_rate=0.85, punt_detection=False),
    "RBI":  CategorySettings("ols",             use_supplemental=True,  time_decay=False, time_decay_rate=0.85, punt_detection=False),
    "SB":   CategorySettings("pairwise_mean",   use_supplemental=True,  time_decay=True,  time_decay_rate=0.90, punt_detection=False),
    "AVG":  CategorySettings("pairwise_mean",   use_supplemental=False, time_decay=False, time_decay_rate=0.85, punt_detection=False),
    "W":    CategorySettings("pairwise_median", use_supplemental=False, time_decay=True,  time_decay_rate=0.80, punt_detection=True),
    "SV":   CategorySettings("robust_reg",      use_supplemental=True,  time_decay=False, time_decay_rate=0.85, punt_detection=False),
    "SO":   CategorySettings("pairwise_mean",   use_supplemental=False, time_decay=False, time_decay_rate=0.85, punt_detection=True),
    "ERA":  CategorySettings("ols",             use_supplemental=True,  time_decay=True,  time_decay_rate=0.80, punt_detection=False),
    "WHIP": CategorySettings("pairwise_mean",   use_supplemental=True,  time_decay=False, time_decay_rate=0.85, punt_detection=False),
}


@dataclass
class SGPConfig:
    """All league constants and model hyperparameters.

    Autoresearch sweeps over the model variant controls.
    """

    # League structure
    n_teams: int = 10
    hitter_slots: int = 15
    pitcher_slots: int = 11
    auction_budget_per_team: int = 360
    min_ip: int = 900

    # Categories
    counting_batting: list = field(default_factory=lambda: ["R", "HR", "RBI", "SB"])
    counting_pitching: list = field(default_factory=lambda: ["W", "SV", "SO"])
    rate_batting: list = field(default_factory=lambda: ["AVG"])
    rate_pitching: list = field(default_factory=lambda: ["ERA", "WHIP"])
    inverse_categories: list = field(default_factory=lambda: ["ERA", "WHIP"])

    # Calibration window
    primary_years: list = field(default_factory=lambda: [2019, 2021, 2022, 2023, 2024, 2025])
    supplemental_years: list = field(default_factory=lambda: [2015, 2016, 2017, 2018])
    excluded_years: list = field(default_factory=lambda: [2020])

    # Model variant controls (autoresearch sweeps these)
    sgp_method: str = "pairwise_mean"  # pairwise_mean, pairwise_median, ols, robust_reg
    use_supplemental: bool = False
    time_decay: bool = False
    time_decay_rate: float = 0.85
    punt_detection: bool = False
    punt_z_threshold: float = -1.5
    replacement_hitter_buffer: int = 50
    replacement_pitcher_buffer: int = 40
    include_keeper_adjustment: bool = False
    inflation_model: str = "uniform"  # uniform, tiered

    # Per-category overrides for composite model (None = use global settings)
    per_category: dict[str, CategorySettings] | None = None

    # Team-level totals for rate stat conversion
    # Derived from data/team_totals.csv, primary years 2019+2021-2025 mean
    team_ab: float = 6514.0
    team_ip: float = 1226.0

    @classmethod
    def composite(cls, **kwargs) -> "SGPConfig":
        """Create config using sweep-derived per-category composite settings.

        The top-level use_supplemental is set True so data loading includes
        supplemental years; per-category filtering happens in compute_sgp().
        """
        defaults = dict(
            sgp_method="composite",
            use_supplemental=True,
            per_category=dict(COMPOSITE_DEFAULTS),
            replacement_hitter_buffer=30,
            replacement_pitcher_buffer=30,
        )
        defaults.update(kwargs)
        return cls(**defaults)

    def effective_config(self, category: str) -> "SGPConfig":
        """Return a config with per-category overrides applied.

        If per_category is None or category has no override, returns self.
        """
        if self.per_category is None or category not in self.per_category:
            return self
        cs = self.per_category[category]
        return replace(
            self,
            sgp_method=cs.sgp_method,
            use_supplemental=cs.use_supplemental,
            time_decay=cs.time_decay,
            time_decay_rate=cs.time_decay_rate,
            punt_detection=cs.punt_detection,
            per_category=None,  # prevent recursion
        )

    @property
    def is_composite(self) -> bool:
        return self.per_category is not None

    @property
    def all_batting(self) -> list:
        return self.counting_batting + self.rate_batting

    @property
    def all_pitching(self) -> list:
        return self.counting_pitching + self.rate_pitching

    @property
    def all_categories(self) -> list:
        return self.all_batting + self.all_pitching

    @property
    def total_auction_pool(self) -> int:
        return self.n_teams * self.auction_budget_per_team

    @property
    def active_years(self) -> list:
        """Years to use for calibration based on current settings."""
        years = list(self.primary_years)
        if self.use_supplemental:
            years = list(self.supplemental_years) + years
        return sorted(years)
