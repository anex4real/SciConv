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
docker load --input test-python-1008-1624.tar
@ECHO Docker Container is running...
docker network ls|Findstr test-python-1008-1624 > $null || docker network create test-python-1008-1624
docker run -it --name test-python-1008-1624 -v test-python-1008-1624:/files test-python-1008-1624:20241008162557 python ./file.py
@ECHO Copping the content of the Container to %execution%
docker cp test-python-1008-1624:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop test-python-1008-1624
@ECHO Removing the docker Container...
start docker rm test-python-1008-1624
@ECHO End!!!
PAUSE
