@ECHO OFF

echo "This script will update Coyote Badger to the newest version."
echo "All of your past projects and custom settings will be saved."
echo "This update may take a minute. Do not close this window while the update is in progress."
pause

call __WINDOWS-STOP.bat
curl -L "https://api.github.com/repos/alexsands/coyote-badger/tarball" -o "cb_next.tar.gz"
tar -xzvf "cb_next.tar.gz"
move "alexsands-coyote-badger-*" "cb_next"
rmdir /s /q "cb_next\_projects"
xcopy /s /e /h /y "cb_next\*" "."
rmdir /s /q "cb_next"
del /q "cb_next.tar.gz"

echo "Coyote Badger is now up to date."
pause
