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
docker load --input bernardo_dl_exp.tar
@ECHO Docker Container is running...
docker network ls|Findstr bernardo_dl_exp > $null || docker network create bernardo_dl_exp
docker run -it --name bernardo_dl_exp -v bernardo_dl_exp:/files bernardo_dl_exp:20241009184513 python hello_1.py
@ECHO Copping the content of the Container to %execution%
docker cp bernardo_dl_exp:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop bernardo_dl_exp
@ECHO Removing the docker Container...
start docker rm bernardo_dl_exp
@ECHO End!!!
PAUSE
