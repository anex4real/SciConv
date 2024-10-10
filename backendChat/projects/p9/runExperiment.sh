#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input p9.tar
echo 'Docker Container is running...'
docker network ls|grep p9 > /dev/null || docker network create p9
docker run -it --name p9 -v p9:/files p9:20241010133852 g++ p9.cpp -o p9 -lm && ./p9
echo 'Copping the content of the Container to' $execution
docker cp p9:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop p9
echo 'Removing the docker Container...'
docker rm p9
echo 'End!!!'
read -p "Press ENTER to close" x
