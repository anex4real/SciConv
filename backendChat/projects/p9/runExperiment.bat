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
docker load --input p9.tar
@ECHO Docker Container is running...
docker network ls|Findstr p9 > $null || docker network create p9
docker run -it --name p9 -v p9:/files p9:20241010133852 g++ p9.cpp -o p9 -lm && ./p9
@ECHO Copping the content of the Container to %execution%
docker cp p9:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop p9
@ECHO Removing the docker Container...
start docker rm p9
@ECHO End!!!
PAUSE
