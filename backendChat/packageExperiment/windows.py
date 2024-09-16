def writeWindowsFIle(rootPath, projectUuid, commands, dockerTagId, hasDatabase, port):
    indexCommand = 0
    arrayFiles = []
    windowsFileLocation = "runExperiment"
    for command in commands:
        if indexCommand != 0:
            myWindowsFileLocation = windowsFileLocation + "_" + str(indexCommand) + ".bat"
        else:
            myWindowsFileLocation = windowsFileLocation + ".bat"

        file = open(rootPath + myWindowsFileLocation, "w", newline='')
        arrayFiles.append(myWindowsFileLocation)

        file.write("@ECHO OFF\n")
        file.write("@ECHO Script is running...\n")
        file.write("set date=%DATE:/=-%\n")
        file.write("set hrs=%time:~0,2%\n")
        file.write("set mns=%time:~3,2%\n")
        file.write("set scs=%time:~6,2%\n")
        file.write("set time=%hrs%-%mns%-%scs%\n")
        file.write("set time=%date%_%time: =%\n")
        # file.write("set timestamp=%DATE:/=-%_%TIME::=-%\n")
        # file.write("set time=%timestamp: =%\n")
        file.write("ECHO %time%\n")
        file.write("set execution=execution_%time%\n")
        file.write("@ECHO Docker Image is loading...\n")

        file.write("docker load --input " + projectUuid + ".tar\n")
        #file.write("docker load < " + projectUuid + ".tar.gz\n")

        file.write("@ECHO Docker Container is running...\n")
        # create database if not exists
        file.write(
            "docker network ls|Findstr " + projectUuid + " > $null || docker network create " + projectUuid + "\n")

        string = "docker run -it --name " + projectUuid

        if indexCommand != 0:
            string += "_" + str(indexCommand)

        if hasDatabase:
            string += " --network=" + projectUuid

        if port is not None:
            string += " -p " + port + ":" + port

        string += " -v " + projectUuid + ":/files " +  dockerTagId + " " + command
        file.write(string + "\n")

        file.write("@ECHO Copping the content of the Container to %execution%\n")
        string = "docker cp " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        string += ":/files ./%execution%"
        file.write(string + "\n")

        file.write("@ECHO Script ended\n")
        file.write("@ECHO Stopping the docker Container...\n")

        string = "docker stop " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        file.write(string + "\n")

        file.write("@ECHO Removing the docker Container...\n")

        string = "start docker rm " + projectUuid
        if indexCommand != 0:
            string += "_" + str(indexCommand)
        file.write(string + "\n")

        file.write("@ECHO End!!!\n")
        file.write("PAUSE\n")
        file.close()

        indexCommand += 1

    return arrayFiles
