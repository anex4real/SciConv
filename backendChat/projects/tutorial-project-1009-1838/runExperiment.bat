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
docker load --input tutorial-project-1009-1838.tar
@ECHO Docker Container is running...
docker network ls|Findstr tutorial-project-1009-1838 > $null || docker network create tutorial-project-1009-1838
docker run -it --name tutorial-project-1009-1838 -v tutorial-project-1009-1838:/files tutorial-project-1009-1838:20241009183913 python ./yahoo_demo.py --res_dir ./res/yahoo/
@ECHO Copping the content of the Container to %execution%
docker cp tutorial-project-1009-1838:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop tutorial-project-1009-1838
@ECHO Removing the docker Container...
start docker rm tutorial-project-1009-1838
@ECHO End!!!
PAUSE
