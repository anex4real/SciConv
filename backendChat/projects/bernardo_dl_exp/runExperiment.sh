#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input bernardo_dl_exp.tar
echo 'Docker Container is running...'
docker network ls|grep bernardo_dl_exp > /dev/null || docker network create bernardo_dl_exp
docker run -it --name bernardo_dl_exp -v bernardo_dl_exp:/files bernardo_dl_exp:20241009184513 python hello_1.py
echo 'Copping the content of the Container to' $execution
docker cp bernardo_dl_exp:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop bernardo_dl_exp
echo 'Removing the docker Container...'
docker rm bernardo_dl_exp
echo 'End!!!'
read -p "Press ENTER to close" x
