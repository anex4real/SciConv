import os


def writeLinuxFile(rootPath, projectUuid, commands, dockerTagId, hasDatabase, port):
    indexCommand = 0
    arrayFiles = []
    LinuxFileLocation = "runExperiment"
    for command in commands:
        if indexCommand != 0:
            myLinuxFileLocation = LinuxFileLocation + "_" + str(indexCommand) + ".sh"
        else:
            myLinuxFileLocation = LinuxFileLocation + ".sh"

        file = open(rootPath + myLinuxFileLocation, "w", newline='')
        arrayFiles.append(myLinuxFileLocation)

        file.write("#!/bin/bash\n")
        file.write("echo 'Script is running...'\n")
        file.write("time=`date +%d-%m-%Y_%H:%M:%S`\n")
        file.write("echo $time\n")
        file.write('execution="execution_$time"\n')
        file.write("echo 'Docker Image is loading...'\n")
        #file.write("docker load < " + projectUuid + ".tar.gz\n")
        file.write("docker load --input " + projectUuid + ".tar\n")
        file.write("echo 'Docker Container is running...'\n")
        # create database if not exists
        file.write(
            "docker network ls|grep " + projectUuid + " > /dev/null || docker network create " + projectUuid + "\n")

        string = "docker run -it --name " + projectUuid

        if indexCommand != 0:
            string += "_" + str(indexCommand)

        if hasDatabase:
            string += " --network=" + projectUuid

        if port is not None:
            string += " -p " + port + ":" + port

        string += " -v " + projectUuid + ":/files " + dockerTagId + " " + command
        file.write(string + "\n")

        file.write("echo 'Copping the content of the Container to' $execution\n")

        string = "docker cp " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        string += ":/files ./$execution"
        file.write(string + "\n")

        file.write("echo 'Script ended'\n")
        file.write("echo 'Stopping the docker Container...'\n")

        string = "docker stop " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        file.write(string + "\n")

        file.write("echo 'Removing the docker Container...'\n")

        string = "docker rm " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        file.write(string + "\n")

        file.write("echo 'End!!!'\n")
        file.write('read -p "Press ENTER to close" x\n')
        file.close()
        # Set permissions to 777
        os.chmod(rootPath + myLinuxFileLocation, 0o777)

        indexCommand += 1

    return arrayFiles
