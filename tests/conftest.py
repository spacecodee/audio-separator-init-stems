import os

os.environ.setdefault("SKIP_MODEL_PRELOAD", "1")
os.environ.setdefault("APP_DIR", "/tmp/audio_separator_app")
os.environ.setdefault("INPUT_DIR", "/tmp/audio_separator_app/input")
os.environ.setdefault("OUTPUT_DIR", "/tmp/audio_separator_app/output")
os.environ.setdefault("MODEL_DIR", "/tmp/audio_separator_app/models")
