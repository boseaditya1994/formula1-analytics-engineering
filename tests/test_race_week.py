from datetime import date

from f1_pipeline.race_week import active_race


def test_active_race_selects_the_current_race_week_only():
    schedule = [
        {"round": "4", "date": "2026-04-05", "raceName": "Japanese Grand Prix"},
        {"round": "5", "date": "2026-04-19", "raceName": "Bahrain Grand Prix"},
    ]
    assert active_race(schedule, date(2026, 4, 3), 2) == schedule[0]
    assert active_race(schedule, date(2026, 4, 6), 2) is None


def test_active_race_prefers_the_nearest_race_when_the_window_has_two():
    schedule = [
        {"round": "1", "date": "2026-04-05"},
        {"round": "2", "date": "2026-04-06"},
    ]
    assert active_race(schedule, date(2026, 4, 5), 1) == schedule[0]
