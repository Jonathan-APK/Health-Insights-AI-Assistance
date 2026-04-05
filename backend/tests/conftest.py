import os


# Disable Langfuse/OTEL exports during tests so pytest runs terminate cleanly
# without network retries or exporter shutdown delays.
os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")