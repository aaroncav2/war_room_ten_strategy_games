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

# Configure Apple Distribution signing ONLY for the main App target's Release build.
# This prevents overriding signing settings for AdMob and Capacitor dependencies.

def find_braced_block(text, opening):
    depth = 0
    in_string = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    i = opening

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == "/" and nxt == "/":
            in_line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            in_block_comment = True
            i += 1
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i

        i += 1

    raise RuntimeError("Unmatched braces in Xcode project")


def get_pbx_object(text, object_id):
    pattern = re.compile(
        r"(?m)^\s*" + re.escape(object_id) +
        r"(?:\s*/\*.*?\*/)?\s*=\s*\{"
    )
    match = pattern.search(text)

    if not match:
        raise RuntimeError("Xcode project object not found: " + object_id)

    opening = text.find("{", match.start())
    closing = find_braced_block(text, opening)
    return opening, closing


# Find the main App target.
app_target_id = None

for match in re.finditer(
    r"(?m)^\s*([A-F0-9]{24})(?:\s*/\*.*?\*/)?\s*=\s*\{", s
):
    object_id = match.group(1)
    opening, closing = get_pbx_object(s, object_id)
    block = s[opening:closing + 1]

    if (
        "isa = PBXNativeTarget;" in block
        and re.search(r"\bname\s*=\s*App\s*;", block)
    ):
        app_target_id = object_id
        break

if not app_target_id:
    raise RuntimeError("Could not find the main App target")

# Find the App target's build configuration list.
_, target_end = get_pbx_object(s, app_target_id)
target_start = s.find("{", s.find(app_target_id))
target_block = s[target_start:target_end + 1]

config_match = re.search(
    r"buildConfigurationList\s*=\s*([A-F0-9]{24})",
    target_block
)

if not config_match:
    raise RuntimeError("App target has no build configuration list")

config_list_id = config_match.group(1)
list_open, list_close = get_pbx_object(s, config_list_id)
config_list = s[list_open:list_close + 1]

configs_match = re.search(
    r"buildConfigurations\s*=\s*\((.*?)\);",
    config_list,
    re.S
)

if not configs_match:
    raise RuntimeError("Could not find App build configurations")

config_ids = re.findall(
    r"\b([A-F0-9]{24})\b",
    configs_match.group(1)
)

# Modify only the Release configuration of the App target.
release_found = False

for config_id in config_ids:
    config_open, config_close = get_pbx_object(s, config_id)
    config_block = s[config_open:config_close + 1]

    if not re.search(r"\bname\s*=\s*Release\s*;", config_block):
        continue

    settings_match = re.search(r"\bbuildSettings\s*=\s*\{", config_block)

    if not settings_match:
        raise RuntimeError("Release configuration has no buildSettings")

    settings_open = config_open + settings_match.end() - 1
    settings_close = find_braced_block(s, settings_open)
    settings = s[settings_open:settings_close + 1]

    identity_pattern = re.compile(
        r'(?m)^([ \t]*)CODE_SIGN_IDENTITY(?:\[[^\]]+\])?\s*=\s*[^;]+;'
    )

    if identity_pattern.search(settings):
        settings = identity_pattern.sub(
            r'\1CODE_SIGN_IDENTITY = "Apple Distribution";',
            settings
        )
    else:
        settings = settings.replace(
            "{",
            '{\n\t\t\t\tCODE_SIGN_IDENTITY = "Apple Distribution";',
            1
        )

    s = s[:settings_open] + settings + s[settings_close + 1:]
    release_found = True
    print("Apple Distribution signing configured for App Release")

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
