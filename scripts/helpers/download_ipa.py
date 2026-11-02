import os
import requests


def download_ipa_from_assets(assets, destination_dir, app_name=None):
    label = f" for {app_name}" if app_name else ""
    ipa_assets = [a for a in assets if a["name"].endswith(".ipa")]

    if not ipa_assets:
        print(f"No .ipa assets found in latest release{label}.")
        return []

    os.makedirs(destination_dir, exist_ok=True)
    downloaded = []

    for asset in ipa_assets:
        ipa_url = asset["browser_download_url"]
        ipa_name = asset["name"]
        dest_path = os.path.join(destination_dir, ipa_name)
        print(f"Downloading {ipa_name} from {ipa_url}")

        try:
            with requests.get(ipa_url, stream=True, timeout=60) as ipa_response:
                if ipa_response.status_code != 200:
                    print(
                        f"Failed to download {ipa_name}. "
                        f"Status code: {ipa_response.status_code}"
                    )
                    continue

                with open(dest_path, "wb") as ipa_file:
                    for chunk in ipa_response.iter_content(chunk_size=8192):
                        ipa_file.write(chunk)

            print(f"Downloaded {ipa_name} successfully.")
            downloaded.append(dest_path)
        except (requests.RequestException, OSError) as e:
            print(f"Download failed for {ipa_name}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)

    return downloaded