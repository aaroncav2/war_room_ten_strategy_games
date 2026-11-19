#!/usr/bin/env python3
"""Patch the generated Capacitor iOS project for AdMob + App Store.
Run after `npx cap add ios` / `npx cap sync ios`. Safe to run repeatedly."""
import os, plistlib, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLIST = os.path.join(ROOT, "ios/App/App/Info.plist")
PBX   = os.path.join(ROOT, "ios/App/App.xcodeproj/project.pbxproj")
ICON_SRC = os.path.join(ROOT, "assets/icon-1024.png")
ICON_DST = os.path.join(ROOT, "ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png")

# Google's public TEST app ID – replaced by your real one via the ADMOB_APP_ID variable.
TEST_APP_ID = "ca-app-pub-3940256099942544~1458002511"
app_id = os.environ.get("ADMOB_APP_ID", "").strip() or TEST_APP_ID

# SKAdNetwork IDs (Google's list). Add/refresh from:
# https://developers.google.com/admob/ios/quick-start#update_your_infoplist
SKAN = """cstr6suwn9 4fzdc2evr5 2fnua5tdw4 ydx93a7ass p78axxw29g v72qych5uu ludvb6z3bs cp8zw746q7
3sh42y64q3 c6k4g5qg8m s39g8k73mm 3qy4746246 hs6bdukanm mlmmfzh3r3 v4nxqhlyqp wzmmz9fp6w su67r6k2v3
yclnxrl5pm 7ug5zh24hu gta9lk7p23 vutu7akeur y5ghdn5j9k n6fk4nfna4 v9wttpbfk9 n38lu8286q 47vhws6wlr
kbd757ywx3 9t245vhmpl a2p9lx4jpn 22mmun2rn5 4468km3ulz 2u9pt9hc89 8s468mfl3y ppxm28t8ap uw77j35x4d
pwa73g5rt2 578prtvx9j 4dzt52r2t5 tl55sbb4fm e5fvkxwrpn 8c4e2ghe7u 3rd42ekr43 97r2b46745 3qcr597p9d""".split()

with open(PLIST, "rb") as f:
    pl = plistlib.load(f)

pl["GADApplicationIdentifier"] = app_id
pl["NSUserTrackingUsageDescription"] = (
    "This lets us show you ads that are more relevant to you. "
    "The game works the same if you say no.")
pl["SKAdNetworkItems"] = [{"SKAdNetworkIdentifier": f"{i}.skadnetwork"} for i in SKAN]
pl["ITSAppUsesNonExemptEncryption"] = False   # only standard HTTPS: skips the export-compliance question
pl["UIRequiredDeviceCapabilities"] = ["arm64"]

with open(PLIST, "wb") as f:
    plistlib.dump(pl, f)
print("Info.plist patched (AdMob app id: %s)" % ("TEST id" if app_id == TEST_APP_ID else app_id))

# iPhone only (avoids needing iPad screenshots in App Store Connect)
with open(PBX, encoding="utf-8") as f:
    s = f.read()
s2 = re.sub(r'TARGETED_DEVICE_FAMILY = "?[0-9,]+"?;', 'TARGETED_DEVICE_FAMILY = 1;', s)
if s2 != s:
    with open(PBX, "w", encoding="utf-8") as f:
        f.write(s2)
print("Device family: iPhone only")

if not release_found:
    raise RuntimeError("App Release configuration was not found")

with open(PBX, "w", encoding="utf-8") as f:
    f.write(s)

print("App Store signing configuration patched successfully")

# App icon
if os.path.exists(ICON_SRC):
    shutil.copyfile(ICON_SRC, ICON_DST)
    print("App icon replaced")
else:
    print("WARNING: assets/icon-1024.png not found, default Capacitor icon kept", file=sys.stderr)
