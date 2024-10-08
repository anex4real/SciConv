#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input test-python-1008-1624.tar
echo 'Docker Container is running...'
docker network ls|grep test-python-1008-1624 > /dev/null || docker network create test-python-1008-1624
docker run -it --name test-python-1008-1624 -v test-python-1008-1624:/files test-python-1008-1624:20241008162557 python ./file.py
echo 'Copping the content of the Container to' $execution
docker cp test-python-1008-1624:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop test-python-1008-1624
echo 'Removing the docker Container...'
docker rm test-python-1008-1624
echo 'End!!!'
read -p "Press ENTER to close" x
