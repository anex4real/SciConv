#!/bin/bash
echo 'Script is running...'
time=`date +%d-%m-%Y_%H:%M:%S`
echo $time
execution="execution_$time"
echo 'Docker Image is loading...'
docker load --input mauricio.tar
echo 'Docker Container is running...'
docker network ls|grep mauricio > /dev/null || docker network create mauricio
docker run -it --name mauricio -v mauricio:/files mauricio:20241008091354 python ./quote_scraper.py https://www.pensador.com/frases_de_grandes_pensadores_que_nos_fazem_pensar_sobre_a_vida/
echo 'Copping the content of the Container to' $execution
docker cp mauricio:/files ./$execution
echo 'Script ended'
echo 'Stopping the docker Container...'
docker stop mauricio
echo 'Removing the docker Container...'
docker rm mauricio
echo 'End!!!'
read -p "Press ENTER to close" x
