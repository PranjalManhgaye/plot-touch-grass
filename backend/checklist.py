"""Turn a TabPFN action into a short outdoor checklist — screen stays short."""

from __future__ import annotations

VERDICTS = {
    "wait": {
        "title": "Stay put today",
        "subtitle": "Frost risk or rough conditions. Prep indoors, go out when the signal flips.",
        "tone": "wait",
    },
    "walk": {
        "title": "Take a walk",
        "subtitle": "Not a planting day — still a good day to leave the screen.",
        "tone": "walk",
    },
    "garden": {
        "title": "Tend the ground",
        "subtitle": "Conditions favor real outdoor work. Put the phone down and use your hands.",
        "tone": "garden",
    },
}


def build_checklist(action: str, features: dict[str, float]) -> list[dict[str, str]]:
    doy = int(features.get("day_of_year", 1))
    season = (
        "early spring"
        if 60 <= doy < 120
        else "late spring"
        if 120 <= doy < 160
        else "summer"
        if 160 <= doy < 250
        else "fall"
        if 250 <= doy < 305
        else "winter"
    )

    if action == "garden":
        items = [
            {
                "step": "01",
                "title": "Step outside for 20 minutes",
                "detail": "No phone scroll. Feel soil temperature with your hand.",
            },
            {
                "step": "02",
                "title": "Work one small bed",
                "detail": f"In {season}, weed, water, or transplant — finish one patch only.",
            },
            {
                "step": "03",
                "title": "Leave a note for next week",
                "detail": "Write what you planted on paper by the door. Come back tomorrow.",
            },
        ]
        if features.get("soil_moisture", 0.5) < 0.35:
            items[1]["detail"] = "Soil looks dry — water deeply once, then mulch."
        if features.get("days_since_last_frost", 0) < 21:
            items.insert(
                1,
                {
                    "step": "01b",
                    "title": "Protect tender starts",
                    "detail": "Frost is recent. Cover seedlings before dusk.",
                },
            )
        return _renumber(items)

    if action == "walk":
        return [
            {
                "step": "01",
                "title": "Walk 30 minutes nearby",
                "detail": "Park, block loop, or trailhead. Headphones optional; screen off.",
            },
            {
                "step": "02",
                "title": "Notice three living things",
                "detail": "Bird, tree, insect — say them out loud. That’s the whole app.",
            },
            {
                "step": "03",
                "title": "Skip the garden beds today",
                "detail": "Wet, windy, or chill. Walking still counts as touching grass.",
            },
        ]

    return [
        {
            "step": "01",
            "title": "Prep tools indoors",
            "detail": "Sharpen pruners, sort seeds, clean pots. Save the yard for a safer day.",
        },
        {
            "step": "02",
            "title": "Check again tomorrow",
            "detail": "Frost and wind shift fast. One minute here, then back outside when clear.",
        },
        {
            "step": "03",
            "title": "Do one indoor plant task",
            "detail": "Repot a houseplant or start seeds on a windowsill — still hands in soil.",
        },
    ]


def _renumber(items: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for i, item in enumerate(items[:4], start=1):
        out.append({**item, "step": f"{i:02d}"})
    return out
