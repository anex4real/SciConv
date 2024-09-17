import json
import os
import time
import flask
import socket
import docker


def makeResponse(response=None, status=200, isJson=False):
    if response is None:
        response = {}
    if isJson:
        mimetype = 'application/json'
        if type(response) != "List":
            response = json.dumps(response)
    else:
        mimetype = flask.Response.default_mimetype

    return flask.Response(response=response, status=status,
                          mimetype=mimetype)


def appendMessage(messages, content=None, contentShort=None, stage=None, role="assistant", jsonObject=False):
    message1 = {"role": role,
                "jsonObject": jsonObject,
                "contentShort": contentShort,
                "content": content}

    if stage is not None:
        message1["stage"] = stage
    messages.append(message1)


def fileIsAnImage(file):
    if file.endswith('.bmp') or file.endswith('.gif') or file.endswith(
            '.jpeg') or file.endswith('.jpg') or file.endswith('.png') or file.endswith('.svg'):
        return True
    else:
        return False


def startDockerClient():
    sock = socket.socket()
    sock.bind(('', 0))
    try:
        client = docker.from_env()
    except Exception as e:
        print(str(e))
        raise Exception("Docker is not running")

    port = sock.getsockname()[1]
    print("Selected Port:" + str(port))
    return {"dockerClient": client, "port": port}


def waitFromMessage(container, message):
    while True:
        if container.status == 'running' or container.status == 'created':
            time.sleep(0.5)
            try:
                container.reload()
                logs = container.logs().decode("utf-8")
                if message in logs:
                    print("Database completed")
                    break
            except Exception as e:
                print(str(e))
                break
        else:
            break


def waitToConclude(container):
    while True:
        if container.status == 'running' or container.status == 'created':
            # await asyncio.sleep(0.5)
            time.sleep(0.5)
            try:
                container.reload()
            except Exception as e:
                print(str(e))
                break
        else:
            break
    return


def createNetworkIfNotExists(dockerClient, networkName):
    allNetworks = dockerClient.networks.list()
    thereIsNetwork = False
    for network in allNetworks:
        if network.name == networkName:
            thereIsNetwork = True
            break
    if not thereIsNetwork:
        # dockerClient.networks.create("network1a", driver="bridge")
        dockerClient.networks.create(name=networkName)


def addWorkdir(myProjectFolder):
    file = open(myProjectFolder + "/Dockerfile", "a")
    file.write("WORKDIR /files\n")
    # f.write("WORKDIR /\n")
    file.write("COPY ./files ./\n\n")
    file.close()


def copyFilesAndClose(file, OSVersion):
    copyFiles(file, OSVersion)
    file.close()


def copyFiles(file, OSVersion):
    if OSVersion is None:
        file.write("# Set the working directory inside the container\n")
        file.write("WORKDIR /files\n")
        file.write("COPY ./files .\n\n")


def convert_json_to_string(input_list):
    converted_list = []

    for message in input_list:
        converted_message = {
            'role': message['role'],
            'content': None
        }

        # Convert content field
        if not isinstance(message['content'], str):
            try:
                converted_message['content'] = json.dumps(message['content'])
            except (TypeError, ValueError):
                converted_message['content'] = str(message['content'])
        else:
            converted_message['content'] = message['content']

        converted_list.append(converted_message)

    return converted_list


def saveDockerImage(myProjectFolder, dockerImageName, dockerTagId):
    try:
        client = docker.from_env()
        image = client.images.get(dockerTagId)
    except Exception as e:
        print(str(e))
        raise Exception("Docker is not running")

    # f = open(myProjectFolder + '/' + dockerImageName + '.tar.gz', 'wb')
    f = open(myProjectFolder + '/' + dockerImageName + '.tar', 'wb')

    for chunk in image.save(named=True):
        f.write(chunk)
    f.close()


def write_file(location, content):
    with open(location, 'w') as file:
        file.write(content)
    print(f"String saved to {location} successfully.")
    print(content)


def snapshot_directory(path):
    files_snapshot = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            stat = os.stat(filepath)
            files_snapshot[filepath] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime
            }
    return files_snapshot


def process_container_diff(diff_list):
    added_files = []
    removed_files = []
    modified_files = []  # You may need additional logic to detect modifications

    for change in diff_list:
        path = change['Path']
        kind = change['Kind']

        if kind == 1:
            if path.startswith("/files"):
                added_files.append(path)
        elif kind == 2:
            removed_files.append(path)
        # For modifications, you may need to use additional logic or tools

    return added_files, removed_files, modified_files

def read_file(location):
    with open(location, 'r') as file:
        content = file.read()

    print(f"Content of {location} read successfully.")
    print(content)
    return content
