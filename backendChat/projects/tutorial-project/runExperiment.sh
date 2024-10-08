#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input tutorial-project.tar
echo 'Docker Container is running...'
docker network ls|grep tutorial-project > /dev/null || docker network create tutorial-project
docker run -it --name tutorial-project -v tutorial-project:/files tutorial-project:20241008081414 python ./yahoo_demo.py --res_dir ./res/yahoo/
echo 'Copping the content of the Container to' $execution
docker cp tutorial-project:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop tutorial-project
echo 'Removing the docker Container...'
docker rm tutorial-project
echo 'End!!!'
read -p "Press ENTER to close" x
