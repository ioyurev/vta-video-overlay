import xml.etree.ElementTree as ET


def process_xml_file(file_path: str):
    tree = ET.parse(file_path)
    contexts = tree.getroot().findall("context")
    for context in contexts:
        name = context.find("name")
        if name and (name.text == "MainWindow"):
            ui_context = context
    messages = ui_context.findall("message")
    for message in messages:
        location = message.find("location")
        if location is not None:
            message.remove(location)
    tree.write(file_path)


if __name__ == "__main__":
    process_xml_file("translation_ru.ts")
