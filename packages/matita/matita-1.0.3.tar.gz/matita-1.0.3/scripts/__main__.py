import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from matita.reference.models import VbaDocs

def main():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s",
        handlers = [logging.FileHandler("logs/matita.log", mode="w")],
    )

    print("Parsing Office VBA Reference...")
    docs = VbaDocs()
    docs.read_directory("office-vba-reference/api")
    print("Analysing Office VBA Reference...")
    docs.process_pages()
    os.makedirs("data", exist_ok=True)
    json.dump(docs.to_dict(), open("data/office-vba-api.json", "wt"), indent=4)
    for app in ["Excel", "Word", "PowerPoint", "Outlook", "Access", "Office"]:
        print(f"Generating matita.office.{app.lower()} module...")
        with open(f"src/matita/office/{app.lower()}.py", "wt") as f:
            f.write(docs.to_python(application=app))

if __name__ == "__main__":
    main()
