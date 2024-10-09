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
docker load --input tutorial_project_1009_1122.tar
@ECHO Docker Container is running...
docker network ls|Findstr tutorial_project_1009_1122 > $null || docker network create tutorial_project_1009_1122
docker run -it --name tutorial_project_1009_1122 -v tutorial_project_1009_1122:/files tutorial_project_1009_1122:20241009112655 python ./yahoo_demo.py --res_dir ./res/yahoo/
@ECHO Copping the content of the Container to %execution%
docker cp tutorial_project_1009_1122:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop tutorial_project_1009_1122
@ECHO Removing the docker Container...
start docker rm tutorial_project_1009_1122
@ECHO End!!!
PAUSE
