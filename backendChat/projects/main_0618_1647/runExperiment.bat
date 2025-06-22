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
docker load --input main_0618_1647.tar
@ECHO Docker Container is running...
docker network ls|Findstr main_0618_1647 > $null || docker network create main_0618_1647
docker run -it --name main_0618_1647 -v main_0618_1647:/files main_0618_1647:20250618164858 python main.py
@ECHO Copping the content of the Container to %execution%
docker cp main_0618_1647:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop main_0618_1647
@ECHO Removing the docker Container...
start docker rm main_0618_1647
@ECHO End!!!
PAUSE
