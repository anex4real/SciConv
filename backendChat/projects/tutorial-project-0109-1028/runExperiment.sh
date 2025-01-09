#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input tutorial-project-0109-1028.tar
echo 'Docker Container is running...'
docker network ls|grep tutorial-project-0109-1028 > /dev/null || docker network create tutorial-project-0109-1028
docker run -it --name tutorial-project-0109-1028 -v tutorial-project-0109-1028:/files tutorial-project-0109-1028:20250109102941 python ./yahoo_demo.py --res_dir ./res/yahoo/
echo 'Copping the content of the Container to' $execution
docker cp tutorial-project-0109-1028:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop tutorial-project-0109-1028
echo 'Removing the docker Container...'
docker rm tutorial-project-0109-1028
echo 'End!!!'
read -p "Press ENTER to close" x
