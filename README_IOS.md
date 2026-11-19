# War Room → iOS App Store (with AdMob banner)

Everything builds in the cloud on GitHub (no Mac needed). The repo contains your game
(`www/index.html`), the AdMob hook (`www/ads.js`), an app icon, and a workflow that builds the
iOS app and uploads it to TestFlight.

Cost: Apple Developer Program is $99/year. GitHub bills macOS build minutes at a higher rate than
Linux on private repos (public repos are free), so check your plan's allowance; one build takes
roughly 10–15 minutes.

---

## 1. Apple Developer account (do this first, approval can take 1–2 days)
1. Enroll at https://developer.apple.com/programs/enroll/ (Individual is fine).
2. Note your **Team ID** (developer.apple.com → Membership details).

## 2. Create the app in Apple's systems
1. developer.apple.com → Certificates, Identifiers & Profiles → Identifiers → **+** → App IDs → App →
   Bundle ID (Explicit), e.g. `com.yourname.warroom`. Write it down; you can't change it later.
2. https://appstoreconnect.apple.com → Apps → **+** → New App → iOS, name **War Room**, pick that
   bundle ID, any SKU.
3. Users and Access → **Integrations** → App Store Connect API → generate a key with **Admin**
   access. Download the `.p8` file (one-time download!). Note the **Key ID** and **Issuer ID**.

## 3. AdMob
1. https://admob.google.com → Apps → Add app → **iOS** → "No, not yet published" is fine.
   Copy the **App ID** (`ca-app-pub-…~…`).
2. In that app → Ad units → Add → **Banner**. Copy the **Ad unit ID** (`ca-app-pub-…/…`).
(Until you add these in step 4, builds show Google's TEST banner. Never click your own live ads.)

## 4. GitHub
1. Create a repo and upload this whole folder (keep the `.github` folder).
2. Repo → Settings → Secrets and variables → Actions → **Secrets** → New:
   - `APPLE_TEAM_ID` – your Team ID
   - `ASC_KEY_ID` – the API Key ID
   - `ASC_ISSUER_ID` – the Issuer ID
   - `ASC_KEY_P8` – open the `.p8` in a text editor and paste the **entire contents**
3. Same page → **Variables** tab → New:
   - `BUNDLE_ID` – e.g. `com.yourname.warroom`
   - `ADMOB_APP_ID` – (optional at first) your AdMob App ID
   - `ADMOB_BANNER_ID` – (optional at first) your banner Ad unit ID
   - `APP_VERSION` – (optional) defaults to `1.0.0`

## 5. Build
Actions tab → **iOS – build and upload to TestFlight** → Run workflow. If it goes green, the build
appears in App Store Connect → TestFlight after ~10–30 min of Apple processing.
If it fails, open the failed step; the logs are also saved as an artifact. Paste the error to me.

## 6. Test on your iPhone
App Store Connect → TestFlight → add yourself as an Internal Tester → install the TestFlight app on
your iPhone → install War Room. Check: the tracking prompt appears once, a test banner shows at the
bottom, nothing is covered by it, sound works, and every game opens and plays.

## 7. Go live with real ads
Set `ADMOB_APP_ID` and `ADMOB_BANNER_ID` (step 4), run the workflow again (each run gets a new build
number automatically). In AdMob, also add your app's `app-ads.txt` later if prompted.

## 8. Store listing and submit
In App Store Connect → your app → version 1.0:
- **Screenshots**: iPhone 6.9" (this build is iPhone-only, so no iPad screenshots needed)
- Description, keywords, support URL, **privacy policy URL** (required; can be a free GitHub Pages page)
- **App Privacy** questionnaire: declare Advertising Data / Device ID / usage data collected by
  AdMob for third-party advertising (and Analytics/Diagnostics as Google describes in its disclosure guide)
- **Age rating** questionnaire (the game's war themes are historical strategy, no gore, answer honestly)
- Select the TestFlight build, then **Submit for Review**

## Notes
- `scripts/patch_ios.py` sets AdMob's ID, the tracking-prompt text, and the SKAdNetwork list.
  Google updates its SKAdNetwork list occasionally, so refresh it from
  https://developers.google.com/admob/ios/quick-start#update_your_infoplist now and then.
- The ad slot: `ads.js` listens for the banner's real height and sets `--ad-h`, so your existing
  bottom spacer in `index.html` grows to fit the ad automatically.
- **Guideline 4.2 (minimum functionality):** Apple rejects "websites in a wrapper". Everything here is
  bundled and works offline, with saved progress and many games, which helps. If review pushes back,
  adding native touches (haptics, share sheet, a native settings screen) is the usual fix.
- To change the icon, replace `assets/icon-1024.png` (1024×1024 PNG, no transparency).
