/* War Room – AdMob banner (iOS). Does nothing in a normal browser.
   The two __TOKENS__ below are filled in by the GitHub Actions build from
   your repo Variables; until you set them, Google's TEST banner is used. */
(function () {
  var BANNER_ID = '__ADMOB_BANNER_ID__';
  var USE_TEST  = '__ADMOB_USE_TEST__';
  var TEST_BANNER_IOS = 'ca-app-pub-3940256099942544/2934735716'; // Google's demo banner
  var RESERVE_DEFAULT = 7; // px kept free when no ad is showing (matches AD_H in index.html)

  var cap = window.Capacitor;
  if (!cap || !cap.isNativePlatform || !cap.isNativePlatform()) return;

  function setAdHeight(px) {
    document.documentElement.style.setProperty('--ad-h', Math.max(RESERVE_DEFAULT, Math.ceil(px || 0)) + 'px');
  }

  async function start() {
    var AdMob = cap.Plugins && cap.Plugins.AdMob;
    if (!AdMob) return;
    try {
      // 1) Consent (Google UMP) – only shows a form where the law requires it (EEA/UK etc.)
      var info = await AdMob.requestConsentInfo();
      if (info.isConsentFormAvailable && info.status === 'REQUIRED') {
        info = await AdMob.showConsentForm();
      }
      if (!info.canRequestAds) return;

      // 2) Apple App Tracking Transparency prompt (shows once, iOS only)
      try {
        var t = await AdMob.trackingAuthorizationStatus();
        if (t && t.status === 'notDetermined') await AdMob.requestTrackingAuthorization();
      } catch (e) {}

      // 3) Start the SDK and show a bottom banner
      await AdMob.initialize();
      AdMob.addListener('bannerAdSizeChanged', function (s) { setAdHeight(s && s.height); });

      var useTest = USE_TEST !== 'false' || BANNER_ID.indexOf('__') === 0;
      await AdMob.showBanner({
        adId: useTest ? TEST_BANNER_IOS : BANNER_ID,
        adSize: 'ADAPTIVE_BANNER',
        position: 'BOTTOM_CENTER',
        margin: 0,
        isTesting: useTest
      });
    } catch (e) {
      console.warn('AdMob start failed', e);
    }
  }

  // Wait until the app is active so the iOS tracking prompt can actually appear.
  window.addEventListener('load', function () { setTimeout(start, 1200); });
})();
