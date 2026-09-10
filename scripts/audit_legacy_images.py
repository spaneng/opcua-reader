"""Read GHCR image history without pulling, rebuilding or changing any image."""
import json
import os
from urllib.request import Request, urlopen


def get(url):
    request = Request(url, headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]})
    with urlopen(request, timeout=30) as response:
        return json.load(response), response.headers.get("Link", "")


url = "https://api.github.com/orgs/spaneng/packages/container/opcua-reader/versions?per_page=100"
records = []
while url:
    versions, links = get(url)
    for version in versions:
        records.append({
            "digest": version["name"],
            "created_at": version["created_at"],
            "tags": version["metadata"]["container"]["tags"],
        })
    url = next((part.split(">", 1)[0].strip().lstrip("<")
                for part in links.split(",") if 'rel="next"' in part), None)
with open("legacy-image-inventory.json", "w") as output:
    json.dump(records, output, indent=2)
# The last legacy release preceded the August 20, 2026 migration.
for record in records:
    if record["created_at"] < "2026-08-20" or record["tags"]:
        print(json.dumps(record))
