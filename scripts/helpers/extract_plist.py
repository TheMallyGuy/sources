import plistlib
import re
import zipfile

_MAIN_PLIST = re.compile(r"^Payload/[^/]+\.app/Info\.plist$")

def get_plist_from_ipa(ipa_path):
    with zipfile.ZipFile(ipa_path, "r") as zip_ref:
        for file_name in zip_ref.namelist():
            if _MAIN_PLIST.match(file_name):
                return plistlib.loads(zip_ref.read(file_name))
    return None