@ECHO OFF
@ECHO Script is running...
set date=%DATE:/=-%
set hrs=%time:~0,2%
set mns=%time:~3,2%
set scs=%time:~6,2%
set time=%hrs%-%mns%-%scs%
set time=%date%_%time: =%
ECHO %time%
set execution=execution_%time%
@ECHO Docker Image is loading...
docker load --input mauricio.tar
@ECHO Docker Container is running...
docker network ls|Findstr mauricio > $null || docker network create mauricio
docker run -it --name mauricio -v mauricio:/files mauricio:20241008091354 python ./quote_scraper.py https://www.pensador.com/frases_de_grandes_pensadores_que_nos_fazem_pensar_sobre_a_vida/
@ECHO Copping the content of the Container to %execution%
docker cp mauricio:/files ./%execution%
@ECHO Script ended
@ECHO Stopping the docker Container...
docker stop mauricio
@ECHO Removing the docker Container...
start docker rm mauricio
@ECHO End!!!
PAUSE
