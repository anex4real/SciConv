#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input ritabash.tar
echo 'Docker Container is running...'
docker network ls|grep ritabash > /dev/null || docker network create ritabash
docker run -it --name ritabash -v ritabash:/files ritabash:20241010105239 chmod +x ./rita.sh && ./rita.sh myfile.txt
echo 'Copping the content of the Container to' $execution
docker cp ritabash:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop ritabash
echo 'Removing the docker Container...'
docker rm ritabash
echo 'End!!!'
read -p "Press ENTER to close" x
