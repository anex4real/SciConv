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
docker load --input ritabash.tar
@ECHO Docker Container is running...
docker network ls|Findstr ritabash > $null || docker network create ritabash
docker run -it --name ritabash -v ritabash:/files ritabash:20241010105239 chmod +x ./rita.sh && ./rita.sh myfile.txt
@ECHO Copping the content of the Container to %execution%
docker cp ritabash:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop ritabash
@ECHO Removing the docker Container...
start docker rm ritabash
@ECHO End!!!
PAUSE
