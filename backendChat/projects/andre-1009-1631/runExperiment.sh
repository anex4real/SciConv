#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input andre-1009-1631.tar
echo 'Docker Container is running...'
docker network ls|grep andre-1009-1631 > /dev/null || docker network create andre-1009-1631
docker run -it --name andre-1009-1631 -v andre-1009-1631:/files andre-1009-1631:20241009163146 python ./main.py
echo 'Copping the content of the Container to' $execution
docker cp andre-1009-1631:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop andre-1009-1631
echo 'Removing the docker Container...'
docker rm andre-1009-1631
echo 'End!!!'
read -p "Press ENTER to close" x
