import os

CONVERTER_FOLDER_PREFIX = "COYOTE_BADGER_CONVERTER-"
PROJECTS_FOLDER = os.path.abspath(os.path.join("_projects"))
PACKAGE_FOLDER = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
SOURCES_TEMPLATE_FILE = os.path.join(PACKAGE_FOLDER, "static", "Sources.xlsx")

PORT = 3000

SEGMENT_WRITE_KEY = "JaFBSHlhMcRfjCovHfFVHIuN5TAj2WkL"

REPO = "alexsands/coyote-badger"
VERSION = "2.2.2"
