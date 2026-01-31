"""
Test Auto-Detection Logic
==========================

Tests the auto_effect() function with various dates to verify
holiday and seasonal detection works correctly.
"""

import sys
from datetime import date

sys.path.insert(0, "..")
from streamlit_effects.utils.auto_detect import get_holiday_name, get_season

# Test dates (matching actual implementation in auto_detect.py)
test_dates = [
    (date(2026, 1, 1), "New Year's Day", "winter"),
    (date(2026, 2, 2), "Groundhog Day", "winter"),
    (date(2026, 2, 14), "Valentine's Day", "winter"),
    (date(2026, 3, 15), None, "spring"),
    (date(2026, 3, 17), "St. Patrick's Day", "spring"),
    (date(2026, 7, 4), "Independence Day (US)", "summer"),
    (date(2026, 10, 31), "Halloween", "fall"),
    (
        date(2026, 12, 24),
        None,
        "winter",
    ),  # Christmas Season (20-26) but get_holiday_name only returns exact match
    (date(2026, 12, 25), "Christmas", "winter"),
    (date(2026, 12, 31), "New Year's Eve", "winter"),
    (date(2026, 6, 15), None, "summer"),
]

print("🧪 Testing Auto-Detection Logic\n")
print("=" * 70)

all_passed = True

for test_date, expected_holiday, expected_season in test_dates:
    detected_holiday = get_holiday_name(test_date)
    detected_season = get_season(test_date)

    # Check holiday
    holiday_match = detected_holiday == expected_holiday
    season_match = detected_season == expected_season

    status = "✅" if (holiday_match and season_match) else "❌"

    print(f"\n{status} Date: {test_date.strftime('%B %d, %Y')}")
    print(
        f"   Holiday: {detected_holiday or 'None':<20} (Expected: {expected_holiday or 'None'})"
    )
    print(f"   Season:  {detected_season:<20} (Expected: {expected_season})")

    if not holiday_match:
        print(f"   ⚠️  Holiday mismatch!")
        all_passed = False
    if not season_match:
        print(f"   ⚠️  Season mismatch!")
        all_passed = False

print("\n" + "=" * 70)

if all_passed:
    print("\n✅ All tests passed! Auto-detection logic is working correctly.")
else:
    print("\n❌ Some tests failed. Check the auto_detect.py implementation.")

# Test today's date
print("\n" + "=" * 70)
print("📅 Today's Detection:")
today = date.today()
today_holiday = get_holiday_name(today)
today_season = get_season(today)

print(f"\nDate:    {today.strftime('%B %d, %Y')}")
print(f"Holiday: {today_holiday or 'None'}")
print(f"Season:  {today_season.title()}")

# Show what effect would be applied
if today_holiday:
    if "New Year" in today_holiday or "Independence" in today_holiday:
        print(f"Effect:  🎆 Fireworks (triggered by {today_holiday})")
    elif "Valentine" in today_holiday:
        print(f"Effect:  💕 Floating Hearts (triggered by {today_holiday})")
    elif "Christmas" in today_holiday:
        print(f"Effect:  ❄️  Snow (triggered by {today_holiday})")
elif today_season == "winter":
    print(f"Effect:  ❄️  Snow (triggered by {today_season.title()} season)")
else:
    print(f"Effect:  None (no effect configured for {today_season.title()} yet)")

print("=" * 70)
