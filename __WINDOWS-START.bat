@ECHO OFF

docker build ^
-t coyotebadger:latest ^
.
docker run ^
-it ^
--rm ^
--name coyotebadger ^
--ipc="host" ^
--shm-size="1gb" ^
--memory="2g" ^
--cpus="2" ^
-v "%CD%/_projects:/opt/coyotebadger/_projects" ^
-p 3000:3000 ^
-p 3001:3001 ^
coyotebadger:latest
