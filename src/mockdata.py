"""Mock evidence so the pipeline runs end-to-end without VideoDB / Bright Data
keys. Realistic-ish snippets for the three demo phones. Swap these out once the
live research agents are wired up — nothing else needs to change.
"""
from __future__ import annotations

from src.schemas import EvidenceItem

_VIDEO = {
    "iPhone 17 Pro": [
        EvidenceItem(source_type="video", source="MKBHD", title="iPhone 17 Pro Review",
                     url="https://youtu.be/iphone17pro-mkbhd", timestamp="04:12",
                     quote="The battery easily gets me through a full heavy day, big step up."),
        EvidenceItem(source_type="video", source="MKBHD", title="iPhone 17 Pro Review",
                     url="https://youtu.be/iphone17pro-mkbhd", timestamp="07:48",
                     quote="Cameras are the best on any phone right now, especially video."),
        EvidenceItem(source_type="video", source="Mrwhosetheboss", title="iPhone 17 Pro - 30 Days Later",
                     url="https://youtu.be/iphone17pro-mwtb", timestamp="03:01",
                     quote="Battery life genuinely impressed me after a month of use."),
        EvidenceItem(source_type="video", source="Mrwhosetheboss", title="iPhone 17 Pro - 30 Days Later",
                     url="https://youtu.be/iphone17pro-mwtb", timestamp="11:20",
                     quote="It's still extremely expensive, that's the main downside."),
        EvidenceItem(source_type="video", source="JerryRigEverything", title="iPhone 17 Pro Durability Test",
                     url="https://youtu.be/iphone17pro-jre", timestamp="06:30",
                     quote="Titanium frame holds up well, scratches at the expected levels."),
    ],
    "Google Pixel 9a": [
        EvidenceItem(source_type="video", source="MKBHD", title="Pixel 9a Review",
                     url="https://youtu.be/pixel9a-mkbhd", timestamp="05:22",
                     quote="The camera punches way above its price, classic Pixel."),
        EvidenceItem(source_type="video", source="Mrwhosetheboss", title="Pixel 9a - Best Value Phone?",
                     url="https://youtu.be/pixel9a-mwtb", timestamp="02:40",
                     quote="For the money the cameras are unbeatable."),
        EvidenceItem(source_type="video", source="Mrwhosetheboss", title="Pixel 9a - Best Value Phone?",
                     url="https://youtu.be/pixel9a-mwtb", timestamp="08:05",
                     quote="The display gets a bit dim outdoors and charging is slow."),
    ],
    "Nothing Phone (3a)": [
        EvidenceItem(source_type="video", source="MKBHD", title="Nothing Phone (3a) Review",
                     url="https://youtu.be/np3a-mkbhd", timestamp="03:55",
                     quote="The design is genuinely fun and stands out, the Glyph is cool."),
        EvidenceItem(source_type="video", source="JerryRigEverything", title="Nothing Phone (3a) Teardown",
                     url="https://youtu.be/np3a-jre", timestamp="04:10",
                     quote="Build is fine for the price but the cameras are just okay."),
    ],
}

_REDDIT = {
    "iPhone 17 Pro": [
        EvidenceItem(source_type="reddit", source="r/iphone", title="17 Pro battery megathread",
                     url="https://reddit.com/r/iphone/17pro_battery",
                     quote="Battery on the 17 Pro is insane, easily 8h screen on time."),
        EvidenceItem(source_type="reddit", source="r/apple", title="Is the 17 Pro worth it?",
                     url="https://reddit.com/r/apple/17pro_worth",
                     quote="Camera is great but $1100 is a hard pill to swallow."),
    ],
    "Google Pixel 9a": [
        EvidenceItem(source_type="reddit", source="r/GooglePixel", title="9a camera samples",
                     url="https://reddit.com/r/googlepixel/9a_camera",
                     quote="The 9a camera embarrasses phones twice its price."),
        EvidenceItem(source_type="reddit", source="r/Android", title="9a long term thoughts",
                     url="https://reddit.com/r/android/9a_longterm",
                     quote="Love the camera, but charging speed is painfully slow."),
    ],
    "Nothing Phone (3a)": [
        EvidenceItem(source_type="reddit", source="r/NothingTech", title="3a after a month",
                     url="https://reddit.com/r/nothingtech/3a_month",
                     quote="Design is awesome but camera in low light is weak."),
    ],
}


def mock_video_evidence(product: str) -> list[EvidenceItem]:
    return list(_VIDEO.get(product, []))


def mock_reddit_evidence(product: str) -> list[EvidenceItem]:
    return list(_REDDIT.get(product, []))
