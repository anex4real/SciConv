#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input tutorial_project_1009_1122.tar
echo 'Docker Container is running...'
docker network ls|grep tutorial_project_1009_1122 > /dev/null || docker network create tutorial_project_1009_1122
docker run -it --name tutorial_project_1009_1122 -v tutorial_project_1009_1122:/files tutorial_project_1009_1122:20241009112655 python ./yahoo_demo.py --res_dir ./res/yahoo/
echo 'Copping the content of the Container to' $execution
docker cp tutorial_project_1009_1122:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop tutorial_project_1009_1122
echo 'Removing the docker Container...'
docker rm tutorial_project_1009_1122
echo 'End!!!'
read -p "Press ENTER to close" x
