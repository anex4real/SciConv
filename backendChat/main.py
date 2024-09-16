# import json
import shutil
from copy import copy
from openai import OpenAI
import os
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS, cross_origin
import settingsPython
from controllers.project import find_files, read_first_50_lines
from packageExperiment.linux import writeLinuxFile
from packageExperiment.windows import writeWindowsFIle
from settings import *
import tempfile

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/project/<projectUuid>/find_files", methods=['GET'])
@cross_origin()
def find_files_project(projectUuid):

    directoryPath = 'projects/' + projectUuid + "/files"
    messagesToUser = []
    messagesToChat = []

    all_files = find_files(directoryPath)

    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": 'The stage of this iteration is: FindProjectFiles'
                        '\nPlease provide a categorized list of Executable Files and Configuration Files.'
                            '\nFormat your response as follows:' 
                            '\n{ "ExecutableFiles": [List of files], "ConfigurationFiles": [List of files] } in valid JSON format.'
                        '\nFor example:' 
                        '\n{ "ExecutableFiles": ["file1.exe", "file2.py", "file3.sh"], "ConfigurationFiles": ["config.yaml"] }'
                            '\nHere are the files to categorize: ' + str(all_files)}
    messagesToUser.append(message1)
    messagesToChat.append(message1)
    try:
        # TODO descomentar
        client = OpenAI()

        completion = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4-turbo",
            messages=
                messagesToChat

        )
        messageText = completion.choices[0].message.content


        # TODO comentar
        # messageText = '{"ExecutableFiles": ["myfile.py", "main.py"], "ConfigurationFiles": []}'
        # messageText = '{"ExecutableFiles": ["newproject\\\\main.py", "main2.py", "main3.py", "new\\\\main.py", "new\\\\main2.py", "new\\\\main3.py", "new\\\\newnew\\\\main2.py", "new\\\\newnew\\\\main3.py"]}'

        try:
            message2 = {"role": "assistant",
                        "content": json.loads(messageText),
                        "contentShort": None,
                        "jsonObject": True}
        except Exception as e:
            message2 = {"role": "assistant",
                        "contentShort": None,
                        "content": messageText,
                        "jsonObject": False}
        messagesToUser.append(message2)

        return makeResponse(messagesToUser, 201, True)
    except Exception as error:
        #TODO alterar
        message2 = {"role": "assistant",
                    "contentShort": str(error),
                    "content": str(error),
                    "jsonObject": False,
                    "state": "alterar"}
        messagesToUser.append(message2)

        return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/parameters-to-use-confirmation', methods=['POST'])
@cross_origin()
def parameters_to_use_confirmation(projectUuid):
    requestData = json.loads(request.data)

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
        length = len(messagesToChat)
        myMessage = messagesToChat[length - 1]["content"]
    else:
        return makeResponse({'message': 'Messages are missing'}, 404, True)

    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content":  "I will interact with you, and in each iteration, I will inform you of the stage name. "
                            "In the previous phase (ProjectLocation), the user selected the project location, which is the name of a folder.\n"
                            "The stage of this iteration is: ParametersToUse.\n"
                            "Consider the following message and determine if the system has provided a command to run an experiment, "
                            "or if it indicates a desire to change the information from the ProjectLocation stage.\n"
                            "Here are your options:\n"
                            "- Reply 'ParametersToUse' if the system has provided a command to run an experiment.\n"
                            "- Reply 'ProjectLocation' if the system wants to change the information from the ProjectLocation stage.\n"
                            "Message: " + myMessage}
    messagesToUser = []
    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)
    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-4",
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=
        messagesToChat,

    )

    firstMessageText = completion.choices[0].message.content
    # messageText = "NOT UPDATED"
    # messageText = '{"PL": "Python", "PLVersion": "Python 3.10",  "Dependencies": ["numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["numpy==1.21.5", "matplotlib==3.5.1", "scikit-learn==1.2.0"]}'

    print(firstMessageText)

    if firstMessageText == "ParametersToUse":
        message1confirmation = {"role": "system",
                                "jsonObject": False,
                                "content":"The stage of this iteration is: ParametersToUse\n"
                                        "Consider the following message and the available files on the project that you provided in a previous message. "
                                        "They are inside the ExecutableFiles variable. Extract the command to run an experiment from the following message and "
                                        "verify if it is a valid command taking into account the existing files in the project.\n"
                                        'Message: ' + myMessage + '\n'
                                        "Your answer follows two options:\n"
                                        "- Reply 'ParametersToUse' if this message does not contain a valid command.\n"
                                        "- If this message contains a valid command, your answer should only contain the command to execute the experiment.",
                                "contentShort": None,
                                }

        messagesToChat.append(message1confirmation)
        messagesToChat = convert_json_to_string(messagesToChat)

        client = OpenAI()
        completion = client.chat.completions.create(
            # model="gpt-4",
            # model="gpt-3.5-turbo",
            model="gpt-4-turbo",
            messages=
            messagesToChat,

        )

        messageText = completion.choices[0].message.content
        print(messageText)

        if messageText == "ParametersToUse":
            message2 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": "Please provide a valid command.",
                        "stage": "ParametersToUse"}
        else:
            message2 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": messageText,
                        "stage": "FindConfigurations"}

        messagesToUser.append(message2)
        return makeResponse(messagesToUser, 201, True)
    else:
        ####CONfirmaçao
        message1confirmation = {"role": "system",
                                "jsonObject": False,
                                "content": 'Check if this message contains a new location for the project: "' + myMessage +
                                           '"\nIf yes, provide the folder name. If no, respond with "NO". '
                                           '\nPlease answer in the required format, with a one-word response.',
                                "contentShort": None}
        confirmationMessage = []
        confirmationMessage.append(message1confirmation)
        confirmationMessage = convert_json_to_string(confirmationMessage)

        client = OpenAI()
        completion = client.chat.completions.create(
            # model="gpt-4",
            # model="gpt-3.5-turbo",
            model="gpt-4-turbo",
            messages=
            confirmationMessage,

        )

        messageText = completion.choices[0].message.content
        print(messageText)
        if messageText == "NO":
            message2 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": "Please provide the new location of the project.",
                        "stage": "ProjectLocation"}
        else:
            directoryPath = 'projects/' + messageText
            if os.path.isdir(directoryPath):
                print("Folder exists.")
                message2 = {"role": "system",
                            "jsonObject": False,
                            "contentShort": messageText,
                            "content": messageText,
                            "stage": "ParametersToUse"}
            else:
                print("Folder does not exist.")
                message2 = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "stage": "ProjectLocation",
                            "content": "Folder does not exist."}

        messagesToUser.append(message2)

    # TODO comentar
    # message2 = {"role": "system",
    #             "jsonObject": False,
    #             "contentShort": None,
    #             "content": myMessage,
    #             "stage": "FindConfigurations"}
    #
    # messagesToUser.append(message2)

    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/infer-files-to-run', methods=['POST'])
@cross_origin()
def infer_files_to_run(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)

    if "filenames" in requestData:
        filenames = requestData["filenames"]
        # filenames= ['main.py', 'main2.py', 'main3.py', 'new\\main.py', 'new\\main2.py', 'new\\main3.py', 'new\\newnew\\main2.py', 'new\\newnew\\main3.py']
    else:
        return makeResponse({'message': 'Filenames are missing'}, 404, True)

    # filenames = ['main.py']
    all_files_lines = {}

    for filename in filenames:
        if os.path.isfile(directoryPath + filename):
            lines = read_first_50_lines(directoryPath + filename)
            all_files_lines[filename] = lines
        else:
            print(f"File not found: {filename}")

    # Convert the content to JSON format
    filesContent = json.dumps(all_files_lines, indent=4)

    messagesToUser = []
    # TODO descomentar

    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": 'Objective: Identify the main execution files within a project.'
                           '\nDescription: The main execution files are responsible for initiating the project and typically include other modules or files. While these main files include other files, the reverse is not true—other files do not include the main files. Note that a project may have more than one main execution file.'
                           '\nAction: Please provide a list of potential main execution files based on the structure of the project.'
                }

    messagesToUser.append(message1)
    messagesToChat = copy(message1)
    messagesToChat["content"] = messagesToChat["content"] + str(filesContent)

    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=[
            messagesToChat,
        ]
    )
    messageText = completion.choices[0].message.content
    messageText = messageText.replace("```", "")
    messageText = messageText.replace("json", "")

    # TODO comentar
    # messageText = '{"PL": "Python", "PLVersion": "Python 3.10",  ' \
    #               '"Dependencies": ["numpy", "pandas", "matplotlib", "scipy", "shap," "tqdm"], ' \
    #               '"DependenciesVersion": ["numpy==1.21.2", "pandas==1.3.3", "matplotlib==3.4.3", ' \
    #               '"scipy==1.7.1", "shap==0.40.0," "tqdm==4.62.2"]}'
    print(messageText)
    try:
        message2 = {"role": "assistant",
                    "content": json.loads(messageText),
                    "contentShort": json.loads(messageText),
                    "jsonObject": True}
    except Exception as e:
        message2 = {"role": "assistant",
                    "content": messageText,
                    "contentShort": messageText,
                    "jsonObject": False}
    messagesToUser.append(message2)

    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/find-configurations', methods=['POST'])
@cross_origin()
def read_first_50_lines_project(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)

    if "filenames" in requestData:
        filenames = requestData["filenames"]
        # filenames= ['main.py', 'main2.py', 'main3.py', 'new\\main.py', 'new\\main2.py', 'new\\main3.py', 'new\\newnew\\main2.py', 'new\\newnew\\main3.py']
    else:
        return makeResponse({'message': 'Filenames are missing'}, 404, True)

    # filenames = ['main.py']
    all_files_lines = {}

    for filename in filenames:
        if os.path.isfile(directoryPath + filename):
            lines = read_first_50_lines(directoryPath + filename)
            all_files_lines[filename] = lines
        else:
            print(f"File not found: {filename}")

    # Convert the content to JSON format
    filesContent = json.dumps(all_files_lines, indent=4)

    messagesToUser = []
    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "The current stage of this interaction is: FindConfigurations"
                           '\nGiven the JSON containing the file name and the first 50 lines, please determine the following:'
                           '\nThe programming language of the file. The version of that language. Any dependencies and their versions.'
                           '\nProvide your response in the following format:'
                           '{ "PL": [programming language], "PLVersion": [programming language version],"Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                           '\nEnsure the dependency names are correct. If the provided name is incorrect, adjust it. For example, in Python, to install the sklearn dependency, the correct command is pip install scikit-learn.'
                           '\nMake sure to list the most recent supported version of the programming language, and format the result in JSON.'
                           '\nExample response:'
                           '\n{ "PL": ["Python"], "PLVersion": "Python 3.8", "Dependencies": ["pandas"], "DependenciesVersion": ["pandas==2.2.0"]}'
                }

    messagesToUser.append(message1)
    messagesToChat = copy(message1)
    messagesToChat["content"] = messagesToChat["content"] + str(filesContent)

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=[
            messagesToChat,
        ]
    )
    messageText = completion.choices[0].message.content
    messageText = messageText.replace("```", "")
    messageText = messageText.replace("json", "")

    # TODO comentar
    # messageText = '{"PL": "Python",  "PLVersion": "Python 3.10", "Dependencies": ["numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["numpy==1.21.5", "matplotlib==3.5.1", "scikit-learn==1.2.0"]}'

    print(messageText)
    try:
        message2 = {"role": "assistant",
                    "content": json.loads(messageText),
                    "contentShort": None,
                    "jsonObject": True}
    except Exception as e:
        message2 = {"role": "assistant",
                    "content": messageText,
                    "contentShort": None,
                    "jsonObject": False}
    messagesToUser.append(message2)

    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/find-configurations-change', methods=['POST'])
@cross_origin()
def find_configurations_change(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        length = len(messagesToChat)
        myMessage = messagesToChat[length - 1]["content"]
    else:
        return makeResponse({'message': 'Messages are missing'}, 404, True)

    messagesToUser = []
    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "The current stage of this interaction is: FindConfigurationsInteraction "
                           '\nCheck if the content of the following message is positive or if the user wants to make changes:'
                           "\nMessage: " + myMessage +
                           '\nConsider the following three options: '
                           '\nReply with "BuildDockerFile" if the content is positive.'
                           '\nReply with "WaitChatInteraction" if the content is negative, but no changes are proposed.'
                           '\nIf the user wants to make changes, implement the proposed changes and provide your response in the following format: '
                           '{ "PL": [programming language], "PLVersion": [programming language version], "Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                           '\nIf the user wants to make changes, ensure the response is in the specified JSON format. If no changes are requested, the response should be a single word.'
                }

    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=
        messagesToChat,

    )
    messageText = completion.choices[0].message.content
    print(messageText)

    if messageText == "BuildDockerFile" or messageText == "WaitChatInteraction":
        message2 = {"role": "assistant",
                    "content": messageText,
                    "contentShort": None,
                    "jsonObject": False,
                    "stage": messageText}
    else:
        messageText = messageText.replace("```", "")
        messageText = messageText.replace("json", "")
        try:
            message2 = {"role": "assistant",
                        "content": json.loads(messageText),
                        "contentShort": None,
                        "jsonObject": True}
        except Exception as e:
            message2 = {"role": "assistant",
                        "content": messageText,
                        "contentShort": None,
                        "jsonObject": False}
    messagesToUser.append(message2)
    return makeResponse(messagesToUser, 201, True)

    # TODO comentar
    # messageText = '{"PL": "Python", "PLVersion": "Python 3.10",  "Dependencies": ["numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["numpy==1.21.5", "matplotlib==3.5.1", "scikit-learn==1.2.0"]}'

    print(messageText)
    try:
        message2 = {"role": "assistant",
                    "content": json.loads(messageText),
                    "contentShort": None,
                    "jsonObject": True}
    except Exception as e:
        message2 = {"role": "assistant",
                    "content": messageText,
                    "contentShort": None,
                    "jsonObject": False}
    messagesToUser.append(message2)

    return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/build-docker-file-chat", methods=['POST'])
@cross_origin()
def buildDockerFileChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
    else:
        return makeResponse({'message': 'Messages are missing'}, 404, True)

    messagesToUser = []
    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "The stage of this interaction is: BuildDockerFile. "
                           'Please use the information I have provided, such as the dependencies, their versions (DependenciesVersion), programming languages (PL), and programming language versions (PLVersion), to build a Dockerfile. '
                           'All the files I want to use are located in the files folder. Inside the container, I want all the files to remain in the files folder as well. '
                           'Therefore, the following two commands should be used: '
                           '"WORKDIR /files" and "COPY files/ ."'
                           '\nDo not use any additional COPY commands. '
                           'In previous messages, I provided the names of the configuration files (configurationFiles) present in the project. '
                           'You may use them if relevant, but it’s not necessary to include COPY or ADD commands for these files, as they have already been copied. '
                           'Please do not infer the names of any files not explicitly provided. '
                           'I only need the Dockerfile required to build the Docker image, so do not include the `CMD` or `ENTRYPOINT` commands in this Dockerfile. '
                           'Provide only the created Dockerfile, as I will use your response directly—no additional text or explanation is needed.'}

    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)
    messageText = ''

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-4",
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=
        messagesToChat,

    )

    messageText = completion.choices[0].message.content
    messageText = messageText.replace("```", "")
    messageText = messageText.replace("Dockerfile", "")
    messageText = messageText.replace("dockerfile", "")

    #####COnfirmaçao1
    messageVerify = {"role": "system",
                     "jsonObject": False,
                     "contentShort": None,
                     "content": 'Please verify that the content is a valid Dockerfile. '
                                '\nEnsure that all specified filenames exist when executing scripts to install dependencies or configure the system to avoid errors. '
                                'Do not execute commands for non-existent files. '
                                'All project files can be found in the `configurationFiles` field from previous messages. '
                                'Do not include any `COPY` commands other than "COPY files/ .". '
                                'Do not add any `WORKDIR` commands other than "WORKDIR /files". '
                                'Additionally, avoid using "CMD", "AND", or "ENTRYPOINT" commands. '
                                'Make the necessary changes and provide only the updated Dockerfile. '
                                'Here is the Dockerfile:' + messageText
                     }

    messagesToChat.append(messageVerify)

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-4",
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=
        messagesToChat,

    )

    messageText = completion.choices[0].message.content

    # TODO comentar
    #     messageText = """# Use the official Python image from the Docker Hub
    # FROM python:3.10-slim
    # # Create a directory for the app
    # WORKDIR /files
    # # Copy all files into the current directory (/usr/src/app) in the image
    # COPY files/ .
    # # Install any dependencies via pip
    # RUN pip install numpy==1.21.5 matplotlib==3.5.1 scikit-learn==1.2.0"""

    write_file(projectPath + "Dockerfile", messageText)

    try:
        message2 = {"role": "assistant",
                    "content": json.loads(messageText),
                    "contentShort": None,
                    "jsonObject": True}
    except Exception as e:
        message2 = {"role": "assistant",
                    "content": messageText,
                    "contentShort": None,
                    "jsonObject": False}
    messagesToUser.append(message2)
    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/chat-interation', methods=['POST'])
@cross_origin()
def chat_interation(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        length = len(messagesToChat)
        myMessage = messagesToChat[length - 1]["content"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
    else:
        return makeResponse({'message': 'Messages are missing'}, 404, True)

    messagesToUser = []

    # TODO descomentar
    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "Evaluate the content of the following message to determine if it is positive, requires changes, or is negative: \n"
                           'Message: ' + myMessage +
                           "\nConsider the following instructions:"
                           '\nIf the message content is positive, reply with "NEXT".'
                           '\nIf the message content is negative but requires no changes, reply with "WaitChatInteraction". '
                           '\nIf changes are needed, respond according to the message type, choosing from the following options: '
                           '\nReply with "FindConfigurationsInteraction" if the message relates to the configuration of the computing environment (e.g., dependency versions or missing programming languages).'
                           '\nReply with "ProjectLocation" if the message involves changing the location of the project .'
                           '\nReply with "ParametersToUse" if the message concerns the command used to run a computational experiment.'
                           "\n\nPlease respond in the specified format. The answer should be exactly one word."
                }

    messagesToUser.append(message1)
    messagesToChat.append(message1)

    messagesToChat = convert_json_to_string(messagesToChat)

    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        messages=
        messagesToChat,

    )
    messageText = completion.choices[0].message.content
    print(messageText)

    message2 = {"role": "assistant",
                "content": messageText,
                "contentShort": None,
                "jsonObject": False,
                "stage": messageText}
    messagesToUser.append(message2)
    return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/build-docker-image-chat", methods=['POST'])
@cross_origin()
def buildDockerImageChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"
    requestData = json.loads(request.data)

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
    else:
        return makeResponse({'message': 'Messages are missing'}, 404, True)

    number_of_attempts = 3
    messagesToUser = []
    errorMessage = ''

    while number_of_attempts > 0:
        try:
            dockerClientResult = startDockerClient()
            dockerClient, port = dockerClientResult["dockerClient"], dockerClientResult["port"]
            number = datetime.now().strftime("%Y%m%d%H%M%S")

            # TODO descomentar
            dockerImageBuilt = dockerClient.images.build(path=projectPath, tag=projectUuid + ":" + number, rm=True)
            dockerImageBuiltFiltered = [s for s in dockerImageBuilt[0].tags if projectUuid in s]
            dockerTagslength = len(dockerImageBuiltFiltered) - 1

            messageText = dockerImageBuiltFiltered[dockerTagslength]

            # TODO comentar
            # messageText = "e25:20240912161423"

            try:
                message1 = {"role": "assistant",
                            "content": json.loads(messageText),
                            "contentShort": None,
                            "jsonObject": True}
            except Exception as e:
                message1 = {"role": "assistant",
                            "content": messageText,
                            "contentShort": None,
                            "jsonObject": False}

            messagesToUser.append(message1)

            return makeResponse(messagesToUser, 201, True)
        except Exception as e:
            print(str(e))
            number_of_attempts -= 1
            dockerfile_content = read_file(projectPath + "Dockerfile")
            message11 = {"role": "system",
                         "jsonObject": False,
                         "contentShort": None,
                         "content": 'The stage of this iteration is: BuildDockerImage '
                                    '\nI have this Dockerfile:' + dockerfile_content +
                                    '\nI tried to build the Docker image, but an error occurred:' + str(e) +
                                    '\nIs the error due to the Dockerfile? If so, just reply "YES".'
                                    'If the problem is not with the Dockerfile, just reply "NO".'
                         }

            messagesToChat = []
            messagesToChat.append(message11)

            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-3.5-turbo",
                model="gpt-4-turbo",
                messages=messagesToChat
            )
            messageText = completion.choices[0].message.content
            if messageText == "YES":
                message21 = {"role": "system",
                             "jsonObject": False,
                             "contentShort": None,
                             "content": 'Provide only the updated Dockerfile as the result because '
                                        'I will use your response as my Dockerfile. Do not include any additional text or explanation.'
                             }

                messagesToChat.append(message21)

                client = OpenAI()
                completion = client.chat.completions.create(
                    # model="gpt-3.5-turbo",
                    model="gpt-4-turbo",
                    messages=messagesToChat
                )
                messageText = completion.choices[0].message.content
                messageText = messageText.replace("```", "")
                messageText = messageText.replace("Dockerfile", "")
                messageText = messageText.replace("dockerfile", "")
                write_file(projectPath + "Dockerfile", messageText)

            else:
                errorMessage = 'An error occurred during the environment build. ' + str(e)
    # errorMessage = 'An error occurred during the build of the environment. ' + "str(e)"
    message2 = {"role": "assistant",
                "content": errorMessage,
                "contentShort": errorMessage,
                "jsonObject": False,
                "stage": "ProjectLocation"}
    messagesToUser.append(message2)

    return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/run-container-chat", methods=['POST'])
@cross_origin()
def runDockerContainerChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)

    if "commandToRun" in requestData:
        commandToRun = requestData["commandToRun"]
    else:
        return makeResponse({"message": "The commandToRun is required"}, 404, True)

    if "dockerImageId" in requestData:
        dockerImageId = requestData["dockerImageId"]
    else:
        return makeResponse({"message": "The command is required"}, 404, True)

    number_of_attempts = 3
    messagesToUser = []

    while number_of_attempts > 0:
        try:
            dockerClientResult = startDockerClient()
            dockerClient, port = dockerClientResult["dockerClient"], dockerClientResult["port"]

            projectImage = dockerClient.images.get(dockerImageId)
            now = datetime.now()
            number = now.strftime("%Y%m%d%H%M%S")

            volume_path = './' + dockerImageId.replace(":", "_")

            container = dockerClient.containers.run(
                image=projectImage,
                name=projectUuid + "_" + number,
                command=commandToRun,
                volumes=[volume_path + ':/files'],
                detach=True
            )

            waitToConclude(container)
            containerLogs = container.logs().decode("utf-8")
            print(containerLogs)

            # # Compare snapshots to identify changes
            # added_files = {}
            # removed_files = {}
            # modified_files = {}
            #
            # added_files, removed_files, modified_files = process_container_diff(container.diff())
            # # Create the final JSON object
            # result = {
            #     "result": containerLogs,
            #     # "added_files": added_files,
            #     # "removed_files": removed_files,
            #     # "modified_files": modified_files
            # }
            #
            # # Convert the result to a JSON-formatted string
            # messageText = json.dumps(result)
            # print(messageText)

            # Prepare the message to be sent back to the user
            messagesToUser = [
                {"role": "assistant",
                 "jsonObject": False,
                 "contentShort": 'The logs of the execution are in the next message.',
                 "content": 'The logs of the execution are in the next message.'},

                {"role": "assistant",
                 "content": containerLogs,
                 "contentShort": containerLogs,
                 "jsonObject": False}
            ]

            # changes = container.diff()

            # for change in changes:
            #   print(change['Kind'], change['Path'])

            # created_files = set()

            # for mount in container.attrs['Mounts']:
            #     if mount['Type'] == 'volume':
            #         volume_name = mount['Name']
            #         volume = dockerClient.volumes.get(volume_name)
            #         for file_info in volume.attrs['Mountpoint'].iterdir():
            #             if file_info.is_file():
            #                 created_files.add(str(file_info))

            # for file in created_files:
            #     print(file)

            return makeResponse(messagesToUser, 201, True)
        except Exception as e:
            print(str(e))
            number_of_attempts -= 1
            dockerfile_content = read_file(projectPath + "Dockerfile")
            message11 = {"role": "system",
                         "jsonObject": False,
                         "contentShort": None,
                         "content": 'The stage of this iteration is: RunContainer'
                                    'I have this Dockerfile:' + dockerfile_content +
                                    '\n I built the Docker image, and the build was successful. ' +
                                    'I used the following command to execute this container: ' + commandToRun +
                                    'However, an error occurred during the execution of the container: ' + str(e) +

                                    '\n Consider the following error and classify it according to its origin: '
                                    '- If the problem stems from the construction of the computing environment, such as the version of the dependencies used or the absence of a programming language, then only answer "FindConfigurations"'
                                    '- If the problem stems from negligence in writing the code, such as errors due to missing files or failing to import functions, then only answer "ProjectLocation"'
                                    '- If the problem stems from the command used to run the computational experiment, then only answer "ParametersToUse"'
                                    'Please answer in the required format. The answer should be one word in length. '
                         }

            messagesToChat = []
            messagesToChat.append(message11)

            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-3.5-turbo",
                model="gpt-4-turbo",
                messages=messagesToChat
            )
            messageText = completion.choices[0].message.content
            message2 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": "An error occurred. I propose that we go back and fix it. \n"
                                        "Message: " + str(e),
                        "content": "An error occurred. I propose that we go back and fix it. \n"
                                   "Message: " + str(e),
                        "stage": messageText}

            messagesToUser.append(message2)
            return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/research-artifact-chat", methods=['POST'])
@cross_origin()
def researchArtifactChat(projectUuid):
    projectsLocation = 'projects'
    projectPath = projectsLocation + "/" + projectUuid
    zipFilePath = f"{projectPath}.zip"

    requestData = json.loads(request.data)
    #
    # dockerImageID = "20240820192103"
    # commandToRun = ["python ./main2.py"]

    # Fetch commandToRun from requestData
    if "commandToRun" in requestData:
        commandToRun = requestData["commandToRun"]
    else:
        return makeResponse({"message": "The commandToRun is required"}, 404, True)

    # Fetch dockerImageId from requestData
    if "dockerImageId" in requestData:
        dockerImageID = requestData["dockerImageId"]
    else:
        return makeResponse({"message": "The dockerImageId is required"}, 404, True)

    commandToRun1 = []
    commandToRun1.append(commandToRun)
    # Generate files for Windows and Linux
    arrayFiles = writeWindowsFIle(projectPath + "/", projectUuid, commandToRun1, dockerImageID, False, None)
    arrayFiles += writeLinuxFile(projectPath + "/", projectUuid, commandToRun1, dockerImageID, False, None)

    # TODO descomentar linha1
    saveDockerImage(projectPath, projectUuid, dockerImageID)
    # zip.write(projectPath + "/" + projectUuid + ".tar.gz", "./" + projectUuid + ".tar.gz")

    # Check if the zip file already exists
    if os.path.isfile(zipFilePath):
        raise FileExistsError(f"The zip file '{zipFilePath}' already exists.")

    def ignore_myfolder(directory, files):
        # List of items to ignore
        ignore_list = []

        # Add 'myfolder' to ignore list if it's in the directory
        if 'files' in files:
            ignore_list.append('files')

        # Add 'myfile.txt' to ignore list if it's in the directory
        if 'Dockerfile' in files:
            ignore_list.append('Dockerfile')

        if projectUuid + ".zip" in files:
            ignore_list.append(projectUuid + ".zip")

        return ignore_list

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tempdir:
        # Copy everything from projectPath to the temporary directory, excluding 'myfolder'
        shutil.copytree(projectPath, tempdir, ignore=ignore_myfolder, dirs_exist_ok=True)

        # Create the zip archive from the temporary directory
        shutil.make_archive(projectPath, 'zip', tempdir)

    print(f"Archive created at {projectPath}.zip, excluding 'files'.")

    # Move the zip file to the desired location
    finalZipPath = os.path.join(projectPath, f"{projectUuid}.zip")
    shutil.move(zipFilePath, finalZipPath)

    print(f"All files and folders from '{projectPath}' have been zipped into '{finalZipPath}'.")

    messagesToUser = [
        {"role": "assistant",
         "contentShort": f"The research artifact has been generated and is located in the root directory of our project '{finalZipPath}'",
         "content": f"The research artifact has been generated and is located in the root directory of our project '{finalZipPath}'",
         "jsonObject": False}
    ]

    return makeResponse(messagesToUser, 201, True)

    # return send_from_directory(projectPath, f"{projectUuid}.zip", as_attachment=True, mimetype="application/zip")


if __name__ == '__main__':
    settingsPython.initializeAllPythonVersions()
    # TODO é necssario escrever FLASK_RUN_PORT=8080 nas variaveis de ambiente da execução para a porta a executar ser a correta
    app.run(host='127.0.0.1', port=8080)

    # TODO Correr experiencias com interface grafica
    # Não é necesario ter export no dockerfile, o container tem que ser corrido desta maneira
    # dockerClient.containers.run(image="web:2",  ports={4200:4200}, command="npm run start", name = "ola" + "_" + "4200", detach = True)
    #
