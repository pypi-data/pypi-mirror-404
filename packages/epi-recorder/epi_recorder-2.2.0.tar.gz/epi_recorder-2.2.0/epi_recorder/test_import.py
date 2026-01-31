
try:
    import epi_recorder.api
    print("epi_recorder.api imported successfully")
except ImportError as e:
    print(f"Failed to import epi_recorder.api: {e}")

try:
    import epi_core
    print("epi_core imported successfully")
except ImportError as e:
    print(f"Failed to import epi_core: {e}")

try:
    import epi_cli
    print("epi_cli imported successfully")
except ImportError as e:
    print(f"Failed to import epi_cli: {e}")


