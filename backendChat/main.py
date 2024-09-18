import shutil
import zipfile
from copy import copy
from openai import OpenAI
import os
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS, cross_origin
from controllers.project import find_files, read_first_50_lines
from packageExperiment.linux import writeLinuxFile
from packageExperiment.windows import writeWindowsFIle
from settings import *
import tempfile

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/project/upload-project", methods=['POST'])
@cross_origin()
def upload_file():
    UPLOAD_FOLDER = 'projects'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    messagesToUser = []

    if 'file' not in request.files:
        print("File is missing")
        appendMessage(messagesToUser, contentShort="File is missing", stage="Start")
        return makeResponse(messagesToUser, 201, True)

    file = request.files["file"]

    if file.filename == '':
        print("No selected file")
        appendMessage(messagesToUser, contentShort="No selected file", stage="Start")
        return makeResponse(messagesToUser, 201, True)

    try:
        if file and file.filename.endswith('.zip'):
            # Save the file temporarily
            temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(temp_path)

            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                # Check for folders inside the zip file
                folder_names = set()
                for member in zip_ref.namelist():
                    if member.endswith('/'):  # Check if it's a folder
                        folder_names.add(member.split('/')[0])
                        projectUuid = list(folder_names)[0]

                if not folder_names:
                    print("No folders found in the zip file")
                    appendMessage(messagesToUser, contentShort="No folders found in the zip file", stage="Start")
                    return makeResponse(messagesToUser, 201, True)

                projectLocation = os.path.join(UPLOAD_FOLDER, projectUuid)
                projectLocationRoot = os.path.join(UPLOAD_FOLDER, projectUuid, projectUuid)
                projectLocationFiles = os.path.join(UPLOAD_FOLDER, projectUuid, "files")

                # Extract all files
                zip_ref.extractall(projectLocation)

            os.remove(temp_path)  # Remove the zip file after extraction
            os.rename(projectLocationRoot, projectLocationFiles)

            appendMessage(messagesToUser, content=projectUuid, stage="FindProjectFiles")
            return makeResponse(messagesToUser, 201, True)
        else:
            print("Only zip files are allowed")
            appendMessage(messagesToUser, contentShort="Only zip files are allowed", stage="Start")
            return makeResponse(messagesToUser, 201, True)

    except Exception as e:
        print(str(e))
        appendMessage(messagesToUser, contentShort=str(e), stage="Start")
        return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/find_files", methods=['GET'])
@cross_origin()
def find_files_project(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files"
    messagesToUser = []
    messagesToChat = []

    all_files = find_files(directoryPath)
    numberInteractions = 3
    chatMessage = ""

    try:
        while numberInteractions > 0:
            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chatMessage + 'The stage of this iteration is: FindProjectFiles'
                                                 '\nPlease provide a categorized list of Executable Files and Configuration Files.'
                                                 '\nFormat your response as follows:'
                                                 '\n{ "ExecutableFiles": [List of files], "ConfigurationFiles": [List of files] } in valid JSON format.'
                                                 '\nFor example:'
                                                 '\n{ "ExecutableFiles": ["./file1.exe", "./file2.py", "./file3.sh", "./folder1/file2.py",], "ConfigurationFiles": ["config.yaml"] }'
                                                 '\nHere are the files to categorize: ' + str(all_files)}
            messagesToUser.append(message1)
            messagesToChat.append(message1)
            # TODO descomentar
            client = OpenAI()

            completion = client.chat.completions.create(
                # model="gpt-3.5-turbo",
                # model="gpt-4-turbo",
                model="gpt-4o",
                messages=
                messagesToChat
            )
            messageText = completion.choices[0].message.content
            messageText = messageText.replace("```", "")
            messageText = messageText.replace("json", "")

            # TODO comentar
            # messageText = '{"ExecutableFiles": ["./myfile.py", "main.py"], "ConfigurationFiles": []}'
            # messageText = '{"ExecutableFiles": ["newproject\\\\main.py", "main2.py", "main3.py", "new\\\\main.py", "new\\\\main2.py", "new\\\\main3.py", "new\\\\newnew\\\\main2.py", "new\\\\newnew\\\\main3.py"]}'

            try:
                userMessage = json.loads(messageText)
                if len(userMessage["ExecutableFiles"]) > 0:
                    appendMessage(messagesToUser, content=userMessage,
                                  contentShort="The requirements for running the experiment '" + projectUuid + "' were met",
                                  jsonObject=False, stage="ParametersToUse")
                else:
                    appendMessage(messagesToUser, contentShort="There are no files to execute. ", jsonObject=False,
                                  stage="Start")
                return makeResponse(messagesToUser, 201, True)

            except Exception as e:
                numberInteractions -= 1
                print("numberInteractions" + str(numberInteractions))
                chatMessage = "The previous result is incorrect. Please consider the following information.\n"

    except Exception as error:
        appendMessage(messagesToUser, content=str(error), contentShort=str(error), stage="Start")
        return makeResponse(messagesToUser, 201, True)

    appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/parameters-to-use-confirmation', methods=['POST'])
@cross_origin()
def parameters_to_use_confirmation(projectUuid):
    requestData = json.loads(request.data)
    messagesToUser = []

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
        length = len(messagesToChat)
        myMessage = messagesToChat[length - 1]["content"]
    else:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)
    try:

        message1 = {"role": "system",
                    "jsonObject": False,
                    "contentShort": None,
                    "content": "I will interact with you, and in each iteration, I will inform you of the stage name. "
                               "In the previous phase (ProjectLocation), the user selected the project location, which is the name of a folder.\n"
                               "The stage of this iteration is: ParametersToUse.\n"
                               "Consider the following message and determine if the system has provided a command to run an experiment, "
                               "or if it indicates a desire to change the information from the ProjectLocation stage.\n"
                               "Here are your options:\n"
                               "- Reply 'ParametersToUse' if the system has provided a command to run an experiment.\n"
                               "- Reply 'ProjectLocation' if the system wants to change the information from the ProjectLocation stage.\n"
                               "Message: " + myMessage}
        messagesToUser.append(message1)
        messagesToChat.append(message1)
        messagesToChat = convert_json_to_string(messagesToChat)
        # TODO descomentar
        client = OpenAI()
        completion = client.chat.completions.create(
            # model="gpt-4",
            # model="gpt-3.5-turbo",
            # model="gpt-4-turbo",
            model="gpt-4o",
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
                                    "content": "The stage of this iteration is: ParametersToUse\n"
                                               "Consider the following message and the available files on the project that you provided in a previous message. "
                                               "They are inside the ExecutableFiles variable. Extract the command to run an experiment from the following message and "
                                               "check that it is a valid command, taking into account the files in the project and the language syntax.\n"
                                               'Message: ' + myMessage + '\n'
                                                                         "Your answer follows two options:\n"
                                                                         "- Reply 'ParametersToUse' if this message does not contain a valid command.\n"
                                                                         "- If this message contains a valid command to be run inside a container in TTY mode, your reply should only include the command to be used in Unix-like systems.",
                                    "contentShort": None,
                                    }

            messagesToChat.append(message1confirmation)
            messagesToChat = convert_json_to_string(messagesToChat)

            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-4",
                # model="gpt-3.5-turbo",
                model="gpt-4-turbo",
                #model="gpt-4o",
                messages=
                messagesToChat,

            )

            messageText = completion.choices[0].message.content
            print(messageText)

            if messageText == "ParametersToUse":
                appendMessage(messagesToUser, contentShort="Please provide a valid command.", stage="ParametersToUse")
            else:
                appendMessage(messagesToUser, content=messageText,
                              contentShort="I will use this command to execute the experiment.\n '"
                                           "Command: '"+ messageText + "'",
                              stage="FindConfigurations")
            return makeResponse(messagesToUser, 201, True)
        else:
            ####CONfirmaçao
            message1confirmation = {"role": "system",
                                    "jsonObject": False,
                                    "content": 'Check if this message contains a new location for the project: "' + myMessage +
                                               '"\nIf yes, provide the folder name. If no, respond with "NO". '
                                               '\nPlease answer in the required format, with a one-word response.',
                                    "contentShort": None}
            confirmationMessage = [message1confirmation]
            confirmationMessage = convert_json_to_string(confirmationMessage)

            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-4",
                # model="gpt-3.5-turbo",
                # model="gpt-4-turbo",
                model="gpt-4o",
                messages=
                confirmationMessage,

            )

            messageText = completion.choices[0].message.content
            print(messageText)
            if messageText == "NO":
                appendMessage(messagesToUser, contentShort="Please provide the new location of the project.",
                              stage="ProjectLocation")
            else:
                directoryPath = 'projects/' + messageText
                if os.path.isdir(directoryPath):
                    print("Folder exists.")
                    appendMessage(messagesToUser, content=messageText,
                                  contentShort="The location of the project has been changed to " + messageText,
                                  stage="ParametersToUse")
                else:
                    print("Folder does not exist.")
                    appendMessage(messagesToUser, contentShort="Folder does not exist.", stage="ProjectLocation")

        # TODO comentar
        # message2 = {"role": "system",
        #             "jsonObject": False,
        #             "contentShort": None,
        #             "content": myMessage,
        #             "stage": "FindConfigurations"}
        #
        # messagesToUser.append(message2)

        return makeResponse(messagesToUser, 201, True)
    except Exception as error:
        print(str(error))
        appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
        return makeResponse(messagesToUser, 201, True)


# @app.route('/project/<projectUuid>/infer-files-to-run', methods=['POST'])
# @cross_origin()
# def infer_files_to_run(projectUuid):
#     directoryPath = 'projects/' + projectUuid + "/files/"
#     requestData = json.loads(request.data)
#     messagesToUser = []
#
#     if "filenames" in requestData:
#         filenames = requestData["filenames"]
#         # filenames= ['main.py', 'main2.py', 'main3.py', 'new\\main.py', 'new\\main2.py', 'new\\main3.py', 'new\\newnew\\main2.py', 'new\\newnew\\main3.py']
#     else:
#         appendMessage(messagesToUser, contentShort='Filenames are missing', stage="Start")
#         return makeResponse(messagesToUser, 201, True)
#
#     # filenames = ['main.py']
#     all_files_lines = {}
#
#     for filename in filenames:
#         if os.path.isfile(directoryPath + filename):
#             lines = read_first_50_lines(directoryPath + filename)
#             all_files_lines[filename] = lines
#         else:
#             print(f"File not found: {filename}")
#
#     # Convert the content to JSON format
#     filesContent = json.dumps(all_files_lines, indent=4)
#
#     # TODO descomentar
#
#     message1 = {"role": "system",
#                 "jsonObject": False,
#                 "contentShort": None,
#                 "content": 'Objective: Identify the main execution files within a project.'
#                            '\nDescription: The main execution files are responsible for initiating the project and typically include other modules or files. '
#                            'While these main files include other files, the reverse is not true—other files do not include the main files. Note that a project may have more than one main execution file.'
#                            '\nAction: Please provide a list of potential main execution files based on the structure of the project.'
#                 }
#
#     messagesToUser.append(message1)
#     messagesToChat = copy(message1)
#     messagesToChat["content"] = messagesToChat["content"] + str(filesContent)
#
#     client = OpenAI()
#     completion = client.chat.completions.create(
#         # model="gpt-3.5-turbo",
#         # model="gpt-4-turbo",
#         model="gpt-4o",
#         messages=[
#             messagesToChat,
#         ]
#     )
#     messageText = completion.choices[0].message.content
#     messageText = messageText.replace("```", "")
#     messageText = messageText.replace("json", "")
#
#     # TODO comentar
#     # messageText = '{"PL": "Python", "PLVersion": "Python 3.10",  ' \
#     #               '"Dependencies": ["numpy", "pandas", "matplotlib", "scipy", "shap," "tqdm"], ' \
#     #               '"DependenciesVersion": ["numpy==1.21.2", "pandas==1.3.3", "matplotlib==3.4.3", ' \
#     #               '"scipy==1.7.1", "shap==0.40.0," "tqdm==4.62.2"]}'
#     print(messageText)
#     try:
#         appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True, stage="BuildDockerFile")
#     except Exception as e:
#         message2 = {"role": "assistant",
#                     "content": messageText,
#                     "contentShort": messageText,
#                     "jsonObject": False}
#     messagesToUser.append(message2)
#
#     return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/find-configurations', methods=['POST'])
@cross_origin()
def find_configurations(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)
    messagesToUser = []

    if "filenames" in requestData:
        filenames = requestData["filenames"]
        # filenames= ['main.py', 'main2.py', 'main3.py', 'new\\main.py', 'new\\main2.py', 'new\\main3.py', 'new\\newnew\\main2.py', 'new\\newnew\\main3.py']
    else:
        appendMessage(messagesToUser, contentShort='filenames are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

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

    numberInteractions = 3
    chatMessage = ""

    try:
        while numberInteractions > 0:
            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chatMessage + "The current stage of this interaction is: FindConfigurations"
                                                 '\nGiven the JSON containing the file name and the first 50 lines, please determine the following:'
                                                 '\nThe programming language of the file. The version of that language. Any dependencies and their versions.'
                                                 '\nProvide your response in the following format:'
                                                 '{ "PL": [all the programming languages used], "PLVersion": [all the programming language version],"Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                                                 '\nEnsure the dependency names are correct. If the provided name is incorrect, adjust it. For example, in Python, to install the sklearn dependency, the correct command is pip install scikit-learn.'
                                                 '\nMake sure to list the most recent supported version of the programming language, and format the result in JSON.'
                                                 '\nExample response:'
                                                 '\n{ "PL": ["Python"], "PLVersion": "Python 3.8", "Dependencies": ["pandas"], "DependenciesVersion": ["pandas==2.2.0"]}'
                        }

            messagesToUser.append(message1)
            myMessage = copy(message1)
            myMessage["content"] = myMessage["content"] + str(filesContent)
            messagesToChat = [myMessage]

            # TODO descomentar
            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-3.5-turbo",
                # model="gpt-4-turbo",
                model="gpt-4o",
                messages=
                    messagesToChat,

            )
            messageText = completion.choices[0].message.content
            messageText = messageText.replace("```", "")
            messageText = messageText.replace("json", "")

            # TODO comentar
            # messageText = '{"PL": "Python",  "PLVersion": "Python 3.10", "Dependencies": ["tqdm", "pandas", "shap","numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["shap==0.41.0", "numpy==1.23.4", "pandas==1.5.2", "scipy==1.9.3", "matplotlib==3.6.2", "tqdm==4.64.1"]}'

            print(messageText)
            try:
                appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True, stage="BuildDockerFile")
                return makeResponse(messagesToUser, 201, True)
            except Exception as e:
                numberInteractions -= 1
                print("numberInteractions" + str(numberInteractions))
                chatMessage = "The previous result is incorrect. Please consider the following information.\n"

    except Exception as error:
        appendMessage(messagesToUser, content=str(error), contentShort=str(error), stage="Start")
        return makeResponse(messagesToUser, 201, True)

    appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/find-configurations-change', methods=['POST'])
@cross_origin()
def find_configurations_change(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)
    messagesToUser = []
    messagesToChat = []

    if "myMessage" in requestData:
        myMessage = requestData["myMessage"]
    else:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "The current stage of this interaction is: FindConfigurationsInteraction "
                           "\nCheck if the content of the user's action in the following message is positive or if the user wants to make changes."
                           "\nMessage: " + myMessage +
                           '\nConsider the following three options: '
                           '\nReply with "BuildDockerFile" if the content is positive.'
                           '\nReply with "WaitChatInteraction" if the content is negative, but no changes are proposed.'
                           '\nIf the user wants to make changes, implement the proposed changes and provide your response in the following format: '
                           '{ "PL": [programming language], "PLVersion": [programming language version], "Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                           '\nIf the user wants to make changes, ensure the response is in the specified JSON format. '
                           'If no changes are requested, the response should be a single word.'
                }

    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        # model="gpt-4-turbo",
        model="gpt-4o",
        messages=
        messagesToChat,

    )
    messageText = completion.choices[0].message.content
    print(messageText)

    if messageText == "BuildDockerFile" or messageText == "WaitChatInteraction":
        appendMessage(messagesToUser, content=messageText, stage=messageText)
    else:
        messageText = messageText.replace("```", "")
        messageText = messageText.replace("json", "")
        try:
            appendMessage(messagesToUser, content=json.loads(messageText),jsonObject=True, stage="WaitChatInteraction")
            return makeResponse(messagesToUser, 201, True)
        except Exception as e:
            numberInteractions = 3
            chatMessage = ""
            while numberInteractions > 0:
                message1 = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "content": chatMessage +
                                       "\nI'll give you a message, and based on the settings used and the actions taken by the user, make the necessary changes."
                                       "\nMessage: " + myMessage +
                                       '\nImplement the proposed changes and provide your response in the following format: '
                                       '{ "PL": [programming language], "PLVersion": [programming language version], "Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                                       '\nEnsure the response is in the specified JSON format. '
                            }
                messagesToChat.append(message1)


                # TODO descomentar
                client = OpenAI()
                completion = client.chat.completions.create(
                    # model="gpt-3.5-turbo",
                    # model="gpt-4-turbo",
                    model="gpt-4o",
                    messages=
                        messagesToChat,

                )
                messageText = completion.choices[0].message.content
                messageText = messageText.replace("```", "")
                messageText = messageText.replace("json", "")

                # TODO comentar
                # messageText = '{"PL": "Python",  "PLVersion": "Python 3.10", "Dependencies": ["tqdm", "pandas", "shap","numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["shap==0.41.0", "numpy==1.23.4", "pandas==1.5.2", "scipy==1.9.3", "matplotlib==3.6.2", "tqdm==4.64.1"]}'

                print(messageText)
                try:
                    appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True,
                                  stage="BuildDockerFile")
                    return makeResponse(messagesToUser, 201, True)
                except Exception as e:
                    numberInteractions -= 1
                    print("numberInteractions" + str(numberInteractions))
                    chatMessage = "The previous result is incorrect. Please consider the following information.\n"

        appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="FindConfigurations")
        # TODO comentar
        # messageText = '{"PL": "Python", "PLVersion": "Python 3.10",  "Dependencies": ["numpy", "matplotlib", "scikit-learn"],  "DependenciesVersion": ["numpy==1.21.5", "matplotlib==3.5.1", "scikit-learn==1.2.0"]}'
        return makeResponse(messagesToUser, 201, True)




@app.route("/project/<projectUuid>/build-docker-file-chat", methods=['POST'])
@cross_origin()
def buildDockerFileChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)
    messagesToUser = []

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
    else:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    message1 = {"role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": "The stage of this interaction is: BuildDockerFile. "
                            "Check if you find this sentence in the conversation history. `I tried to build the Docker image, but an error occurred` "
                            "If so, you have to take the previous docker file into account so that you don't provide the same dockerfile because the previous one had an error."
                           'Please use the information I have provided, such as the dependencies, their versions (DependenciesVersion), programming languages (PL), and programming language versions (PLVersion), to build a Dockerfile. '
                           'All the files I want to use are located in the files folder. Inside the container, I want all the files to remain in the files folder as well. '
                           'Therefore, the following two commands should be used: '
                           '"WORKDIR /files" and "COPY files/ ."'
                           '\nDo not use any additional COPY commands. '
                           'In previous messages, I provided the names of the configuration files (configurationFiles) present in the project. '
                           'You may use them if relevant, but it’s not necessary to include COPY or ADD commands for these files, because they are inside the "./files" folder and have already been copied. '
                           'Please do not infer the names of any files not explicitly provided. '
                           'I only need the Dockerfile required to build the Docker image, so do not include the `CMD` or `ENTRYPOINT` commands in this Dockerfile. '
                           'Provide only the created Dockerfile, as I will use your response directly—no additional text or explanation is needed.'}

    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)
    #messageText = ''

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        # model="gpt-4",
        # model="gpt-3.5-turbo",
        model="gpt-4-turbo",
        # model="gpt-4o",
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
                                'Remove all other commands that copy information.'
                                'Do not add any `WORKDIR` commands other than "WORKDIR /files". '
                                'Remove all other commands that use the `WORKDIR` command. '
                                'Remove all other commands that use "CMD", "AND", or "ENTRYPOINT" commands. '
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
        # model="gpt-4o",
        messages=
        messagesToChat,

    )

    messageText = completion.choices[0].message.content

    # TODO comentar
    #     messageText = """FROM python:3.10
    #
    # WORKDIR /files
    # COPY files/ .
    #
    # RUN pip install shap==0.41.0 numpy==1.23.4 pandas==1.5.2 scipy==1.9.3 matplotlib==3.6.2 tqdm==4.64.1"""

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
    messagesToUser = []

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
        length = len(messagesToChat)
        myMessage = messagesToChat[length - 1]["content"]
        # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
    else:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    numberInteractions = 3
    chatMessage = ""

    try:
        while numberInteractions > 0:
            # TODO descomentar
            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chatMessage + "Please evaluate the following message content: "
                                                 "If the message propose possible changes, reply with 'CHANGE' "
                                                 "If the message is positive or indicates agreement, respond with 'NEXT' "
                                                 "If the message is negative and indicates disagreement, but does not propose possible changes, respond with 'WaitChatInteraction' "
                                                 "\nPlease respond in the specified format. The answer should be exactly one word."
                                                 "\nMessage: `" + myMessage + "`"
                        }
            messagesToUser.append(message1)
            messagesToChat.append(message1)

            messagesToChat = convert_json_to_string(messagesToChat)

            client = OpenAI()
            completion = client.chat.completions.create(
                # model="gpt-3.5-turbo",
                # model="gpt-4-turbo",
                model="gpt-4o",
                messages=
                messagesToChat,

            )
            messageText = completion.choices[0].message.content
            print(messageText)

            # TODO aqui dá erro quando respondo apenas no
            palavras = messageText.split()
            if len(palavras) == 1:
                if messageText == "CHANGE":
                    message1 = {"role": "system",
                                "jsonObject": False,
                                "contentShort": None,
                                "content": chatMessage + 'Please evaluate the following message. '
                                                         '\nReply with "FindConfigurationsInteraction" if the message relates to the configuration of the computing environment (e.g., dependency versions or missing programming languages).'
                                                         '\nReply with "ProjectLocation" if the message involves changing the location of the project .'
                                                         '\nReply with "ParametersToUse" if the message concerns the command used to run a computational experiment.'
                                                         "\n\nPlease respond in the specified format. The answer should be exactly one word."
                                                         '\nMessage: "' + myMessage + '"'
                                }

                    messagesToUser.append(message1)
                    messagesToChat.append(message1)

                    messagesToChat = convert_json_to_string(messagesToChat)

                    client = OpenAI()
                    completion = client.chat.completions.create(
                        # model="gpt-3.5-turbo",
                        # model="gpt-4-turbo",
                        model="gpt-4o",
                        messages=
                        messagesToChat,

                    )
                    messageText = completion.choices[0].message.content
                    print(messageText)

                    words = messageText.split()
                    if len(words) == 1:
                        appendMessage(messagesToUser, content=messageText, stage=messageText)
                        return makeResponse(messagesToUser, 201, True)
                    else:
                        chatMessage = "The previous result is incorrect. Please consider the following information.\n"
                        numberInteractions -= 1
                        print("numberInteractions" + str(numberInteractions))
                else:
                    appendMessage(messagesToUser, content=messageText, stage=messageText)
                    return makeResponse(messagesToUser, 201, True)
            else:
                chatMessage = "The previous result is incorrect. Please consider the following information.\n"
                numberInteractions -= 1
                print("numberInteractions" + str(numberInteractions))
                # appendMessage(messagesToUser, content=str(e), contentShort=str(e), stage="Start")

    except Exception as error:
        appendMessage(messagesToUser, content=str(error), contentShort=str(error), stage="Start")
        return makeResponse(messagesToUser, 201, True)

    appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
    return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/build-docker-image-chat", methods=['POST'])
@cross_origin()
def buildDockerImageChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"
    requestData = json.loads(request.data)
    messagesToUser = []

    if "messages" in requestData:
        messagesToChat = requestData["messages"]
    else:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

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
        # messageText = "e25:20240917151400"
        # raise Exception("gcc: error: -E or -x required when input is from standard input")

        try:
            appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True, stage="RunContainer")
        except Exception as e:
            appendMessage(messagesToUser, content=messageText, stage="RunContainer")

        return makeResponse(messagesToUser, 201, True)
    except Exception as e:
        print(str(e))
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
            # model="gpt-4-turbo",
            model="gpt-4o",
            messages=messagesToChat
        )
        messageText = completion.choices[0].message.content
        if messageText == "YES":
            appendMessage(messagesToUser,
                          content='\nI have this Dockerfile:' + dockerfile_content +
                                  '\nI tried to build the Docker image, but an error occurred:' + str(e),
                          contentShort='An error occurred during the environment build. I propose to try to build a new environment.',
                          stage="FindConfigurations")
        else:
            errorMessage = (
                    "An error occurred during the environment build. \n"
                    "Error: " + str(e) + "\n"
                                         "What might have caused this unexpected result? \n"
                                         "For example: I want to change the execution parameters.\n"
                                         "For example: I want to change the project location.\n"
                                         "For example: I want to change the computing environment used (programming languages, dependencies).\n"
            )
            appendMessage(messagesToUser, contentShort=errorMessage, stage="WaitChatInteraction")

        return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/run-container-chat", methods=['POST'])
@cross_origin()
def runDockerContainerChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)
    messagesToUser = []

    if "commandToRun" in requestData:
        commandToRun = requestData["commandToRun"]
    else:
        appendMessage(messagesToUser, contentShort="The commandToRun is required", stage="BuildDockerFile")
        return makeResponse(messagesToUser, 201, True)

    if "dockerImageId" in requestData:
        dockerImageId = requestData["dockerImageId"]
    else:
        appendMessage(messagesToUser, contentShort="The dockerImageId is required", stage="BuildDockerFile")
        return makeResponse(messagesToUser, 201, True)

    number_of_attempts = 3

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
                volumes=[volume_path + ':/files'],
                detach=True,
                command="/bin/sh",
                tty=True
            )
            # stdin=True: Allows you to pass input to the container via standard input.
            # You often use both together when running fully interactive sessions in containers. For example:
            # container.exec_run('/bin/bash', stdin=True, tty=True)

            #commandToRun= "python ./myfile.py && cd pasta && python ./myfile2.py && cd .. &&  python ./myfile3.py"
            exec_first = container.exec_run('/bin/sh -c "' + commandToRun + '"')

            containerLogs= "Command Output:" + exec_first.output.decode('utf-8') +"\n\n\n"
            exit_code = f"Exit Code: {exec_first.exit_code}\n"
            containerLogs += exit_code

            print(containerLogs)

            container.stop()
            container.remove()

            # waitToConclude(container)
            # containerLogs = container.logs().decode("utf-8")
            # print(containerLogs)

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
                # model="gpt-4-turbo",
                model="gpt-4o",
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
    messagesToUser = []
    #
    # dockerImageID = "20240820192103"
    # commandToRun = ["python ./main2.py"]

    # Fetch commandToRun from requestData
    if "commandToRun" in requestData:
        commandToRun = requestData["commandToRun"]
    else:
        appendMessage(messagesToUser, contentShort="The commandToRun is required", stage="ParametersToUse")
        return makeResponse(messagesToUser, 201, True)

    # Fetch dockerImageId from requestData
    if "dockerImageId" in requestData:
        dockerImageID = requestData["dockerImageId"]
    else:
        appendMessage(messagesToUser, contentShort="The dockerImageId is required", stage="BuildDockerFile")
        return makeResponse(messagesToUser, 201, True)

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
    # TODO é necssario escrever FLASK_RUN_PORT=8080 nas variaveis de ambiente da execução para a porta a executar ser a correta
    app.run(host='0.0.0.0', port=8080)

    # TODO Correr experiencias com interface grafica
    # Não é necesario ter export no dockerfile, o container tem que ser corrido desta maneira
    # dockerClient.containers.run(image="web:2",  ports={4200:4200}, command="npm run start", name = "ola" + "_" + "4200", detach = True)
    #

    # # Initialize the Docker client
    # client = docker.from_env()
    #
    # # Pull the image (optional if already pulled)
    #
    # # Create and start a container (detach=True to keep it running)
    # now = datetime.now()
    # number = now.strftime("%Y%m%d%H%M%S")
    # projectUuid="e255"
    # projectPath = 'projects/' + projectUuid + "/"
    #
    # dockerImageBuilt = client.images.build(path=projectPath, tag=projectUuid + ":" + number, rm=True)
    # dockerImageBuiltFiltered = [s for s in dockerImageBuilt[0].tags if projectUuid in s]
    # dockerTagslength = len(dockerImageBuiltFiltered) - 1
    #
    # messageText = dockerImageBuiltFiltered[dockerTagslength]
    #
    # container = client.containers.run(messageText,name= projectUuid + "_" + number, command="/bin/sh", detach=True, tty=True)
    #
    # # Run the first command
    # exec_first = container.exec_run('/bin/sh -c "python ./myfile.py && cd pasta && python ./myfile2.py && cd .. &&  python ./myfile3.py"')
    # print(exec_first.output.decode('utf-8'))
    #
    # # Get the output
    # output = exec_first.output.decode('utf-8')
    # print("Command Output:")
    # print(output)
    #
    # # Get the exit code
    # exit_code = exec_first.exit_code
    # print(f"Exit Code: {exit_code}")
    #
    # # Stop and remove the container after commands
    # container.stop()
    # #container.remove()
