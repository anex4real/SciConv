#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input mauricio-1008-1458.tar
echo 'Docker Container is running...'
docker network ls|grep mauricio-1008-1458 > /dev/null || docker network create mauricio-1008-1458
docker run -it --name mauricio-1008-1458 -v mauricio-1008-1458:/files mauricio-1008-1458:20241008145907 python ./quote_scraper.py https://www.pensador.com/frases_de_grandes_pensadores_que_nos_fazem_pensar_sobre_a_vida/
echo 'Copping the content of the Container to' $execution
docker cp mauricio-1008-1458:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop mauricio-1008-1458
echo 'Removing the docker Container...'
docker rm mauricio-1008-1458
echo 'End!!!'
read -p "Press ENTER to close" x
