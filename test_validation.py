from pydantic import ValidationError
from models import Wrapped

# Broken on purpose:
#   1. key_artists is a string, not a list
#   2. music_personality is missing
broken_json = """{
  "title": "Test",
  "phases": [{"name": "Metal Era", "start_month": "2026-04", "end_month": "2026-06",
              "key_artists": "BABYMETAL", "description": "Lots of metal"}],
  "discoveries": [],
  "fun_fact": "Nothing"
}"""

# Valid: follows the form exactly
valid_json = """{
  "title": "Test",
  "phases": [{"name": "Metal Era", "start_month": "2026-04", "end_month": "2026-06",
              "key_artists": ["BABYMETAL"], "description": "Lots of metal"}],
  "discoveries": [{"artist": "BABYMETAL", "comment": "New favorite"}],
  "music_personality": {"label": "Explorer", "description": "Likes to switch it up."},
  "fun_fact": "Nothing"
}"""

for name, text in [("broken", broken_json), ("valid", valid_json)]:
    try:
        Wrapped.model_validate_json(text)
        print(f"✅ {name}: passes validation")
    except ValidationError as error:
        print(f"❌ {name}: does not match the form")
        print(error)