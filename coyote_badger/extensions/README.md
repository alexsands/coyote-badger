# Extensions


## bypass-paywall-chrome

This extension helps bypass paywalls when pulling content. It uses
[this Chrome extension](https://github.com/iamadamdev/bypass-paywalls-chrome)
at version 1.7.8 with minor adjustments:

1. Line 201 in `/src/js/background.js` is commented out to prevent the options
page from loading when Playwright launches a browser.
2. This line was removed from line 24 in `/manifest.json` to prevent
auto-updates that may break in the future:
```json
"update_url": "https://raw.githubusercontent.com/iamadamdev/bypass-paywalls-chrome/master/src/updates/updates.xml",
```


## ublock

This extension blocks ads on websites to produce cleaner PDFs. It uses
[this Chrome extension](https://github.com/gorhill/uBlock/)
at version 1.33.2 with no adjustments.
