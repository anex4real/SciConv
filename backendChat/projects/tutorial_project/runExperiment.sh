#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input tutorial_project.tar
echo 'Docker Container is running...'
docker network ls|grep tutorial_project > /dev/null || docker network create tutorial_project
docker run -it --name tutorial_project -v tutorial_project:/files tutorial_project:20241009161418 python ./yahoo_demo.py --res_dir ./res/yahoo/
echo 'Copping the content of the Container to' $execution
docker cp tutorial_project:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop tutorial_project
echo 'Removing the docker Container...'
docker rm tutorial_project
echo 'End!!!'
read -p "Press ENTER to close" x
