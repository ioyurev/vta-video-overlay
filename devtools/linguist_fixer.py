import xml.etree.ElementTree as ET


### For some reason pyside6-linguist becomes unresponsive when trying to select
### a context based on a .ui file, so here's a workaround in the form of removing
### the location information of the strings to be translated in the .ts file
def process_xml_file(file_path: str):
    tree = ET.parse(file_path)
    contexts = tree.getroot().findall("context")
    for context in contexts:
        messages = context.findall("message")
        for message in messages:
            location = message.find("location")
            if location is not None:
                message.remove(location)
    tree.write(file_path)


if __name__ == "__main__":
    process_xml_file("translation_ru.ts")
