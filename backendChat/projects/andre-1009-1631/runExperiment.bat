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
docker load --input andre-1009-1631.tar
@ECHO Docker Container is running...
docker network ls|Findstr andre-1009-1631 > $null || docker network create andre-1009-1631
docker run -it --name andre-1009-1631 -v andre-1009-1631:/files andre-1009-1631:20241009163146 python ./main.py
@ECHO Copping the content of the Container to %execution%
docker cp andre-1009-1631:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop andre-1009-1631
@ECHO Removing the docker Container...
start docker rm andre-1009-1631
@ECHO End!!!
PAUSE
