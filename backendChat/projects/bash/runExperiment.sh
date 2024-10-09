#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input bash.tar
echo 'Docker Container is running...'
docker network ls|grep bash > /dev/null || docker network create bash
docker run -it --name bash -v bash:/files bash:20241009173721 chmod +x config_git.sh && ./config_git.sh
echo 'Copping the content of the Container to' $execution
docker cp bash:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop bash
echo 'Removing the docker Container...'
docker rm bash
echo 'End!!!'
read -p "Press ENTER to close" x
