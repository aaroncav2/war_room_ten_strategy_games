#!/usr/bin/env bash
# Prepares the web assets + native iOS project. Used by the GitHub workflow.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${BUNDLE_ID:?Set the BUNDLE_ID repository variable (e.g. com.yourname.warroom)}"

# 1) bundle id -> capacitor.config.json
node -e '
const fs=require("fs");const c=JSON.parse(fs.readFileSync("capacitor.config.json","utf8"));
c.appId=process.env.BUNDLE_ID;fs.writeFileSync("capacitor.config.json",JSON.stringify(c,null,2)+"\n");'

# 2) ad unit id -> www/ads.js  (test ads unless a real banner id is provided)
if [ -n "${ADMOB_BANNER_ID:-}" ]; then
  sed -i.bak "s#__ADMOB_BANNER_ID__#${ADMOB_BANNER_ID}#; s#__ADMOB_USE_TEST__#false#" www/ads.js
else
  sed -i.bak "s#__ADMOB_USE_TEST__#true#" www/ads.js
fi
rm -f www/ads.js.bak

# 3) native project
[ -d ios ] || npx cap add ios
npx cap sync ios
python3 scripts/patch_ios.py
