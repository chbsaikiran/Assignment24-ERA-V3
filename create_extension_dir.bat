@echo off
mkdir chrome_extension
copy manifest.json chrome_extension\
copy popup.html chrome_extension\
copy popup.js chrome_extension\
copy icon16.png chrome_extension\
copy icon48.png chrome_extension\
copy icon128.png chrome_extension\

echo Chrome extension files have been moved to chrome_extension directory.
echo Please load the extension from the chrome_extension directory.
pause 