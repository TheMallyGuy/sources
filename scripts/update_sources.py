import os
import json
import requests
from helpers.download_ipa import download_ipa_from_assets
from helpers.extract_plist import get_plist_from_ipa

FILE = os.path.dirname(os.path.abspath(__file__))
IPA_DIR = os.path.join(FILE, "..", "ipas")
os.makedirs(IPA_DIR, exist_ok=True)

with open(os.path.join(FILE, "updateSources.json"), "r") as f:
    UPDATE_SOURCES = json.load(f)

RAW_BASE = "https://raw.githubusercontent.com/{}/{}".format(
    os.environ.get("GITHUB_REPOSITORY", "TheMallyGuy/sources"),
    os.environ.get("GITHUB_REF_NAME", "master"),
)

headers = {"Accept": "application/vnd.github+json"}
token = os.environ.get("GITHUB_TOKEN")
if token:
    headers["Authorization"] = f"Bearer {token}"

for source in UPDATE_SOURCES:
    print(f"Pulling new ipa for {source['app']}")

    try:
        response = requests.get(
            f"https://api.github.com/repos/{source['githubRepo']}/releases",
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"Request failed for {source['app']}: {e}")
        continue

    if response.status_code != 200:
        print(
            f"Failed to fetch releases for {source['app']}. "
            f"Status code: {response.status_code}"
        )
        continue

    releases = response.json()
    if not releases:
        print(f"No releases found for {source['app']}.")
        continue

    assets = releases[0].get("assets", [])

    downloaded = download_ipa_from_assets(assets, IPA_DIR, app_name=source["app"])

    for ipa_path in downloaded:
        plist = get_plist_from_ipa(ipa_path)
        if plist is None:
            print(f"No Info.plist found in {os.path.basename(ipa_path)}")
            continue

        print(
            f"Extracted Info.plist for {source['app']}: "
            f"{plist.get('CFBundleIdentifier')} {plist.get('CFBundleShortVersionString')}"
        )

        buildVersion = plist.get("CFBundleVersion")
        if buildVersion is None:
            print(f"No CFBundleVersion found in {os.path.basename(ipa_path)}")
            continue

        shortVersion = plist.get("CFBundleShortVersionString")
        if shortVersion is None:
            print(
                f"No CFBundleShortVersionString found in {os.path.basename(ipa_path)}"
            )
            continue

        new = {
            "name": source["app"],
            "bundleIdentifier": plist.get("CFBundleIdentifier"),
            "developerName": source["developerName"],
            "iconURL": source["iconURL"]
            if source["iconURL"].startswith("http")
            else f"{RAW_BASE}/{source['iconURL'].removeprefix('./')}",
            "localizedDescription": "",
            "versions": [
                {
                    "version": shortVersion,
                    "date": releases[0].get("published_at", ""),
                    "size": os.path.getsize(ipa_path),
                    "buildVersion": buildVersion,
                    "downloadURL": next(
                        a["browser_download_url"]
                        for a in assets
                        if a["name"] == os.path.basename(ipa_path)
                    ),
                }
            ],
        }

        sources_path = os.path.join(FILE, "..", "sources.json")

        with open(sources_path, "r", encoding="utf-8") as f:
            sources = json.load(f)

        apps = sources["apps"]
        existing_app = next(
            (app for app in apps if app["name"] == source["app"]), None
        )
        if existing_app:
            existing_app.update(new)
        else:
            apps.append(new)

        with open(sources_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, indent=2, ensure_ascii=False)
