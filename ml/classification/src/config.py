"""Single source of truth for class labels, paths, and thresholds."""

from pathlib import Path

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "reports_raw.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "reports_clean.csv"
MODELS_DIR = BASE_DIR / "models"

MODEL_VERSION = "event-classifier-v1"
MODEL_PATH = MODELS_DIR / f"{MODEL_VERSION}.joblib"
METADATA_PATH = MODELS_DIR / f"metadata_{MODEL_VERSION}.json"

# ---- Classes ----
EVENT_CLASSES = [
    "flood",
    "heavy_rainfall",
    "thunderstorm",
    "heatwave",
    "fog",
    "dust_storm",
    "strong_wind",
    "cyclone",
    "lightning",
    "hailstorm",
    "other",
]

# ---- Inference ----
CONFIDENCE_THRESHOLD = 0.45  # tuned in Phase 2 evaluation step; see notes below
UNKNOWN_LABEL = "unknown"

# ---- Reproducibility ----
RANDOM_STATE = 42
TEST_SIZE = 0.15
VAL_SIZE = 0.15  # taken out of the remaining train set
