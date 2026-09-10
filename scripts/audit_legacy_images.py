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

# Inspect OCI labels, not timestamps alone, to identify compatible source code.
import base64
import hashlib
import sys
from urllib.parse import urlencode

preserve = "--preserve" in sys.argv
scope = "repository:spaneng/opcua-reader:pull" + (",push" if preserve else "")
credentials = base64.b64encode(
    (os.environ["GITHUB_ACTOR"] + ":" + os.environ["GH_TOKEN"]).encode()
).decode()
request = Request("https://ghcr.io/token?" + urlencode({"service": "ghcr.io", "scope": scope}),
                  headers={"Authorization": "Basic " + credentials})
with urlopen(request, timeout=30) as response:
    registry_token = json.load(response)["token"]
registry = "https://ghcr.io/v2/spaneng/opcua-reader/"
accept = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


def registry_get(path):
    request = Request(registry + path, headers={
        "Authorization": "Bearer " + registry_token, "Accept": accept,
    })
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    return raw, json.loads(raw)


def put_tag(tag, raw, manifest):
    request = Request(registry + "manifests/" + tag, data=raw, method="PUT", headers={
        "Authorization": "Bearer " + registry_token,
        "Content-Type": manifest["mediaType"],
    })
    with urlopen(request, timeout=30) as response:
        assert response.status == 201
    reread, _ = registry_get("manifests/" + tag)
    assert hashlib.sha256(reread).digest() == hashlib.sha256(raw).digest()
    print("Verified tag", tag, "sha256:" + hashlib.sha256(raw).hexdigest())


targets = {
    "fuel_additive": "0a2c3340255f738b957cda29ebdfa9f104848902",
    "dv1": "e6f7e6571f503b3cc7d29792dfb1428b28fd8c2b",
}
verified = {}
for record in records:
    if not (record["created_at"].startswith("2026-01-18") or "dv1" in record["tags"]):
        continue
    raw, manifest = registry_get("manifests/" + record["digest"])
    if "manifests" not in manifest:
        continue
    revisions = set()
    architectures = set()
    for child in manifest["manifests"]:
        platform = child.get("platform", {})
        if platform.get("os") != "linux" or platform.get("architecture") not in ("arm64", "amd64"):
            continue
        _, image = registry_get("manifests/" + child["digest"])
        _, config = registry_get("blobs/" + image["config"]["digest"])
        revisions.add(config.get("config", {}).get("Labels", {}).get("org.opencontainers.image.revision"))
        architectures.add(platform["architecture"])
    print("Image provenance", record["digest"], sorted(architectures), list(revisions))
    for tag, expected in targets.items():
        if revisions == {expected} and architectures == {"arm64", "amd64"}:
            verified[tag] = (record["digest"], raw, manifest)
assert set(verified) == set(targets), "Both legacy images must be verified before any tag changes"
summary = {tag: {"digest": value[0], "commit": targets[tag]} for tag, value in verified.items()}
with open("legacy-image-provenance.json", "w") as output:
    json.dump(summary, output, indent=2)
if preserve:
    # Save the displaced image before restoring the previously published 1.0 tag.
    old_raw, old_manifest = registry_get("manifests/fuel_additive")
    old_digest = hashlib.sha256(old_raw).hexdigest()
    put_tag("archive-fuel-additive-" + old_digest[:12], old_raw, old_manifest)
    for tag, (digest, raw, manifest) in verified.items():
        put_tag("legacy-" + tag.replace("_", "-") + "-" + targets[tag][:7], raw, manifest)
    # Historical deployment compose files still refer to this mutable tag.
    # Restore its verified old contents without recreating any running container.
    _, raw, manifest = verified["fuel_additive"]
    put_tag("fuel_additive", raw, manifest)
