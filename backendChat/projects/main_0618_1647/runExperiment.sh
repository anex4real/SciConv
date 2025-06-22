#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input main_0618_1647.tar
echo 'Docker Container is running...'
docker network ls|grep main_0618_1647 > /dev/null || docker network create main_0618_1647
docker run -it --name main_0618_1647 -v main_0618_1647:/files main_0618_1647:20250618164858 python main.py
echo 'Copping the content of the Container to' $execution
docker cp main_0618_1647:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop main_0618_1647
echo 'Removing the docker Container...'
docker rm main_0618_1647
echo 'End!!!'
read -p "Press ENTER to close" x
