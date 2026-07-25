from pathlib import Path
import re


### For some reason pyside6-linguist becomes unresponsive when trying to select
### a context based on a .ui file, so here's a workaround in the form of removing
### the location information of the strings to be translated in the .ts file
def process_xml_file(file_path: str):
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    # Remove <location ... /> lines
    content = re.sub(r"^[ \t]*<location[^>]*/>\s*\n?", "", content, flags=re.MULTILINE)

    # Ensure XML header and DOCTYPE TS are present
    if not content.startswith("<?xml"):
        content = '<?xml version="1.0" encoding="utf-8"?>\n' + content

    if "<!DOCTYPE TS>" not in content:
        lines = content.splitlines()
        if lines and lines[0].startswith("<?xml"):
            lines.insert(1, "<!DOCTYPE TS>")
        else:
            lines.insert(0, "<!DOCTYPE TS>")
        content = "\n".join(lines)

    content = content.rstrip("\n") + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    process_xml_file("translation_ru.ts")
