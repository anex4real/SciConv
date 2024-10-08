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
docker load --input tutorial-project.tar
@ECHO Docker Container is running...
docker network ls|Findstr tutorial-project > $null || docker network create tutorial-project
docker run -it --name tutorial-project -v tutorial-project:/files tutorial-project:20241008081414 python ./yahoo_demo.py --res_dir ./res/yahoo/
@ECHO Copping the content of the Container to %execution%
docker cp tutorial-project:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop tutorial-project
@ECHO Removing the docker Container...
start docker rm tutorial-project
@ECHO End!!!
PAUSE
