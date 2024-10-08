#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input tutorial-project-10080908.tar
echo 'Docker Container is running...'
docker network ls|grep tutorial-project-10080908 > /dev/null || docker network create tutorial-project-10080908
docker run -it --name tutorial-project-10080908 -v tutorial-project-10080908:/files tutorial-project-10080908:20241008090906 python ./yahoo_demo.py --res_dir ./res/yahoo/
echo 'Copping the content of the Container to' $execution
docker cp tutorial-project-10080908:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop tutorial-project-10080908
echo 'Removing the docker Container...'
docker rm tutorial-project-10080908
echo 'End!!!'
read -p "Press ENTER to close" x
