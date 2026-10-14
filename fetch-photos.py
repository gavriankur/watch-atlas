"""Compatibility entry point for the current catalog workflow."""
import pathlib, runpy
runpy.run_path(str(pathlib.Path(__file__).parent / "scripts" / "cache-photos.py"), run_name="__main__")
