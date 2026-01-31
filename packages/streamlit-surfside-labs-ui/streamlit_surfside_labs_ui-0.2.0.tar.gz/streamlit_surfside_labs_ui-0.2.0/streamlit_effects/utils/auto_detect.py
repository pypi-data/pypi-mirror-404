"""
Auto-detection utility for seasonal and holiday effects.

Automatically applies appropriate effects based on the current date,
including major holidays and seasonal changes.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any


def auto_effect(
    enable: bool = True, intensity: str = "medium", **kwargs: Any
) -> Optional[str]:
    """
    Automatically apply an effect based on the current date.

    Detects major holidays and seasons to apply appropriate visual effects.
    Supports both Northern and Southern hemisphere seasons (configurable).

    Args:
        enable: Enable auto-detection (set False to disable)
        intensity: Default intensity for effects ("light", "medium", "heavy")
        **kwargs: Additional arguments passed to the detected effect

    Returns:
        Name of the effect applied, or None if no effect was triggered

    Example:
        ```python
        import streamlit as st
        from streamlit_effects import auto_effect

        st.title("My App")

        # Automatically apply seasonal/holiday effect
        effect_name = auto_effect()
        if effect_name:
            st.sidebar.info(f"🎨 Today's effect: {effect_name}")
        ```

    Holiday/Event Detection:
        - New Year's Day (Jan 1): Fireworks
        - Valentine's Day (Feb 14): Floating Hearts
        - Groundhog Day (Feb 2): Groundhog effect (future)
        - St. Patrick's Day (Mar 17): Shamrocks (future)
        - Independence Day US (Jul 4): Fireworks
        - Halloween (Oct 31): Spooky effects (future)
        - Christmas Season (Dec 20-26): Snow
        - New Year's Eve (Dec 31): Fireworks

    Seasonal Detection (Northern Hemisphere):
        - Winter (Dec-Feb): Snow
        - Spring (Mar-May): Flowers (future)
        - Summer (Jun-Aug): Butterflies (future)
        - Fall (Sep-Nov): Falling leaves (future)
    """
    if not enable:
        return None

    # Import effect functions (lazy import to avoid circular dependencies)
    from ..effects.snow import snow
    from ..effects.confetti import confetti
    from ..effects.fireworks import fireworks
    from ..effects.hearts import floating_hearts

    today = date.today()
    month = today.month
    day = today.day

    # Merge kwargs with default intensity
    effect_kwargs = {"intensity": intensity, **kwargs}

    # === MAJOR HOLIDAYS (Exact Date Matches) ===

    # New Year's Day
    if month == 1 and day == 1:
        fireworks(**effect_kwargs)
        return "fireworks"

    # Valentine's Day
    if month == 2 and day == 14:
        floating_hearts(**effect_kwargs)
        return "floating_hearts"

    # Groundhog Day (placeholder for future groundhog effect)
    # if month == 2 and day == 2:
    #     groundhog_day(**effect_kwargs)
    #     return "groundhog_day"

    # St. Patrick's Day (placeholder for future shamrock effect)
    # if month == 3 and day == 17:
    #     shamrocks(**effect_kwargs)
    #     return "shamrocks"

    # Independence Day (US)
    if month == 7 and day == 4:
        fireworks(**effect_kwargs)
        return "fireworks"

    # Halloween (placeholder for future spooky effect)
    # if month == 10 and day == 31:
    #     spooky(**effect_kwargs)
    #     return "spooky"

    # Christmas Season (Dec 20-26)
    if month == 12 and 20 <= day <= 26:
        snow(**effect_kwargs)
        return "snow"

    # New Year's Eve
    if month == 12 and day == 31:
        fireworks(**effect_kwargs)
        return "fireworks"

    # === SEASONAL EFFECTS (Northern Hemisphere) ===

    # Winter (December, January, February)
    if month in [12, 1, 2]:
        snow(**effect_kwargs)
        return "snow"

    # Spring (March, April, May) - placeholder for future flower effect
    # if month in [3, 4, 5]:
    #     flowers(**effect_kwargs)
    #     return "flowers"

    # Summer (June, July, August) - placeholder for future butterfly effect
    # if month in [6, 7, 8]:
    #     butterflies(**effect_kwargs)
    #     return "butterflies"

    # Fall/Autumn (September, October, November) - placeholder for future leaves effect
    # if month in [9, 10, 11]:
    #     falling_leaves(**effect_kwargs)
    #     return "falling_leaves"

    # No effect triggered
    return None


def get_holiday_name(target_date: Optional[date] = None) -> Optional[str]:
    """
    Get the name of the holiday for a given date.

    Args:
        target_date: Date to check (defaults to today)

    Returns:
        Holiday name if found, None otherwise

    Example:
        ```python
        from streamlit_effects.utils.auto_detect import get_holiday_name
        from datetime import date

        # Check today
        holiday = get_holiday_name()
        if holiday:
            st.write(f"Happy {holiday}!")

        # Check specific date
        holiday = get_holiday_name(date(2026, 12, 25))
        # Returns "Christmas"
        ```
    """
    if target_date is None:
        target_date = date.today()

    month = target_date.month
    day = target_date.day

    holidays = {
        (1, 1): "New Year's Day",
        (2, 2): "Groundhog Day",
        (2, 14): "Valentine's Day",
        (3, 17): "St. Patrick's Day",
        (7, 4): "Independence Day (US)",
        (10, 31): "Halloween",
        (12, 25): "Christmas",
        (12, 31): "New Year's Eve",
    }

    return holidays.get((month, day))


def get_season(target_date: Optional[date] = None, hemisphere: str = "north") -> str:
    """
    Get the current season for a given date and hemisphere.

    Args:
        target_date: Date to check (defaults to today)
        hemisphere: "north" or "south" hemisphere

    Returns:
        Season name: "winter", "spring", "summer", or "fall"

    Example:
        ```python
        from streamlit_effects.utils.auto_detect import get_season

        season = get_season()
        st.write(f"Current season: {season}")
        ```
    """
    if target_date is None:
        target_date = date.today()

    month = target_date.month

    # Northern Hemisphere
    if hemisphere.lower() in ["north", "northern", "n"]:
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "fall"

    # Southern Hemisphere (seasons are opposite)
    else:
        if month in [12, 1, 2]:
            return "summer"
        elif month in [3, 4, 5]:
            return "fall"
        elif month in [6, 7, 8]:
            return "winter"
        else:  # 9, 10, 11
            return "spring"
