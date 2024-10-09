@ECHO OFF
@ECHO Script is running...
set date=%DATE:/=-%
set hrs=%time:~0,2%
set mns=%time:~3,2%
set scs=%time:~6,2%
set time=%hrs%-%mns%-%scs%
set time=%date%_%time: =%
ECHO %time%
set execution=execution_%time%
@ECHO Docker Image is loading...
docker load --input bash.tar
@ECHO Docker Container is running...
docker network ls|Findstr bash > $null || docker network create bash
docker run -it --name bash -v bash:/files bash:20241009173721 chmod +x config_git.sh && ./config_git.sh
@ECHO Copping the content of the Container to %execution%
docker cp bash:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop bash
@ECHO Removing the docker Container...
start docker rm bash
@ECHO End!!!
PAUSE
