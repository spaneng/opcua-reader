#!/bin/sh
set -eu

uv export --frozen --no-dev --no-editable --quiet -o requirements.txt
rm -rf packages_export
uv pip install \
    --no-deps \
    --no-installer-metadata \
    --no-compile-bytecode \
    --python-platform aarch64-manylinux_2_28 \
    --python 3.13 \
    --quiet \
    --target packages_export \
    --refresh \
    -r requirements.txt

# When no wheel matches the target platform uv falls back to building the sdist
# on the build host, so a macOS box quietly produces macOS binaries. That only
# surfaces as an ImportError inside the lambda, so catch it here instead.
foreign=$(find packages_export -name '*.so' -exec file {} + | grep -v 'ELF 64-bit LSB .*ARM aarch64' || true)
if [ -n "$foreign" ]; then
    echo "error: non-aarch64-linux binaries in packages_export:" >&2
    echo "$foreign" >&2
    exit 1
fi

rm -f package.zip
(cd packages_export && zip -rq ../package.zip .)
zip -rq package.zip src

echo "Built package.zip"
