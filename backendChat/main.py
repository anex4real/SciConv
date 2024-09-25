import shutil
import zipfile
from copy import copy
from openai import OpenAI
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS, cross_origin
from packageExperiment.linux import writeLinuxFile
from packageExperiment.windows import writeWindowsFIle
from settings import *
import tempfile

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/", methods=['get'])
@cross_origin()
def home():
    messagesToUser = [
        {"role": "assistant",
         "contentShort": f"HOME PAGE",
         "content": f"HOME PAGE",
         "jsonObject": False}
    ]
    return makeResponse(messagesToUser, 201, True)


@app.route("/project/upload-project", methods=['POST'])
@cross_origin()
def upload_file():
    UPLOAD_FOLDER = 'projects'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    messagesToUser = []
    messagesToChat = []

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

            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": "I need to validate the variable 'projectUuid' for use in this function. "
                                   "\nIf 'projectUuid' is a valid Docker tag name, respond with 'YES'."
                                   "\nIf it's not valid, return an updated, valid version of 'projectUuid'."
                                   "\nCurrent value: projectUuid = " + projectUuid + ".\n"
                                                                                     "The function to execute is: dockerClient.images.build(path=projectPath, tag=projectUuid) and do not support the simbol '-' and capital letters. "
                                                                                     "Your response should be exactly one word, either 'YES' or the updated 'projectUuid' value."}
            messagesToChat.append(message1)
            messagesToChat = convert_json_to_string(messagesToChat)
            # TODO descomentar
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                # model="gpt-4o",
                # model="chatgpt-4o-latest",
                messages=
                messagesToChat,

            )

            firstMessageText = completion.choices[0].message.content
            if firstMessageText == "Yes":
                appendMessage(messagesToUser, content=projectUuid, stage="FindProjectFiles")
            else:
                newprojectLocation = os.path.join(UPLOAD_FOLDER, firstMessageText)
                os.rename(projectLocation, newprojectLocation)
                appendMessage(messagesToUser, content=firstMessageText, stage="FindProjectFiles")

            return makeResponse(messagesToUser, 201, True)
        else:
            print("Only zip files are allowed")
            appendMessage(messagesToUser, contentShort="Only zip files are allowed", stage="Start")
            return makeResponse(messagesToUser, 201, True)

    except Exception as e:
        print(str(e))
        appendMessage(messagesToUser, contentShort=str(e), stage="Start")
        return makeResponse(messagesToUser, 201, True)


@app.route("/project/find_files", methods=['POST'])
@cross_origin()
def find_files_project():
    requestData = json.loads(request.data)

    if "possibleProjectUuid" in requestData:
        possibleProjectUuid = requestData["possibleProjectUuid"]

    askmessage = {"role": "system",
                  "jsonObject": False,
                  "contentShort": None,
                  "content": "Analyze the following message and determine whether it contains a possible folder name."
                             '\nMessage: ' + possibleProjectUuid +
                             '\nIf it does, please provide the folder name. If it does not, respond with "NO"'
                             '\nPlease answer in the required format, with a one-word response.'}

    # TODO descomentar
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        ## model="gpt-4o",
        # model="chatgpt-4o-latest",
        messages=
        [askmessage]
    )
    projectUuid = completion.choices[0].message.content

    print("possibleProjectUuid:" + projectUuid)
    messagesToUser = []
    messagesToChat = []

    if projectUuid == "NO":
        appendMessage(messagesToUser, contentShort="Please enter a valid location", stage="Start")
        return makeResponse(messagesToUser, 201, True)

    directoryPath = 'projects/' + projectUuid + "/files"
    all_files = find_files(directoryPath)
    number_interactions = 3
    chat_message = ""

    try:
        while number_interactions >= 0:
            userContent = (
                    chat_message +
                    'The stage of this iteration is: FindProjectFiles.\n' +
                    'The current task is to classify the provided list of files into two categories:\n' +
                    '1. Executable Files: Files that can be executed to perform a specific task (e.g., .exe, .sh, .py).\n' +
                    '2. Configuration/Installation Files: Files that contain information used to configure the execution of other files or install software components (e.g., .yaml, .json, .cfg, .ini, .deb).\n' +
                    'Some files may not belong to either category and can be left out.\n' +
                    'Please format your response in valid JSON as follows:\n' +
                    '{"ExecutableFiles": [List of executable files], "ConfigurationFiles": [List of configuration and installation files]}\n' +
                    'For example:\n' +
                    '{ "ExecutableFiles": ["./file1.exe", "./file2.py", "./file3.sh", "./folder1/file2.py"], ' +
                    '"ConfigurationFiles": ["config.yaml", "setup.ini", "install.deb"] }\n' +
                    'If a file does not fit into either category, do not include it in the response.'
            )

            chatContent = userContent + '\nHere are the name of the files to classify: ' + str(all_files)

            message_user = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "content": userContent}
            message_chat = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "content": chatContent}

            messagesToUser.append(message_user)
            messagesToChat.append(message_chat)

            # TODO descomentar
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                # model="gpt-4o",
                # model="chatgpt-4o-latest",
                messages=
                messagesToChat
            )
            messageText = completion.choices[0].message.content
            messageText = messageText.replace("```", "")
            messageText = messageText.replace("json", "")
            print("find_files_project" + messageText)

            # TODO comentar
            # messageText = '{"ExecutableFiles": ["./myfile.py", "main.py"], "ConfigurationFiles": []}'
            # messageText = '{"ExecutableFiles": ["newproject\\\\main.py", "main2.py", "main3.py", "new\\\\main.py", "new\\\\main2.py", "new\\\\main3.py", "new\\\\newnew\\\\main2.py", "new\\\\newnew\\\\main3.py"]}'

            try:
                userMessage = json.loads(messageText)
                if len(userMessage["ExecutableFiles"]) > 0:
                    userMessage["ProjectUuid"] = projectUuid
                    appendMessage(messagesToUser, content=userMessage,
                                  contentShort="We've found your project.\n The project is in folder " + projectUuid + "\n",
                                  stage="ParametersToUse")
                else:
                    appendMessage(messagesToUser, contentShort="There are no files to execute. ",
                                  stage="Start")
                return makeResponse(messagesToUser, 201, True)

            except Exception as e:
                number_interactions -= 1
                print("number_interactions" + str(number_interactions))
                print("Error:" + str(e))
                chat_message = ("The previous result is incorrect. I got this error:" + str(e) +
                                "\nPlease consider the following information.\n")

    except Exception as error:
        appendMessage(messagesToUser, content="I got this error:" + str(error),
                      contentShort="I got this error:" + str(error), stage="Start")
        return makeResponse(messagesToUser, 201, True)

    appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
    return makeResponse(messagesToUser, 201, True)


@app.route('/project/<projectUuid>/parameters-to-use-confirmation', methods=['POST'])
@cross_origin()
def parameters_to_use_confirmation(projectUuid):
    requestData = json.loads(request.data)
    messagesToUser = []

    if "messages" not in requestData:
        appendMessage(messagesToUser, contentShort='Messages are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    messagesToChat = requestData["messages"]
    # messages= ['projects/newproject\\main.py', 'projects/newproject\\main2.py', 'projects/newproject\\main3.py', 'projects/newproject\\new\\main.py', 'projects/newproject\\new\\main2.py', 'projects/newproject\\new\\main3.py', 'projects/newproject\\new\\newnew\\main2.py', 'projects/newproject\\new\\newnew\\main3.py']
    length = len(messagesToChat)
    myMessage = messagesToChat[length - 1]["content"]

    try:

        message1confirmation = {
            "role": "system",
            "jsonObject": False,
            "content": (
                    "The stage of this iteration is: ParametersToUse\n"
                    "Consider the following message and the available files in the project that you provided in a previous message. "
                    "These files are stored inside the `ExecutableFiles` variable. Extract the command to run an experiment from the following message and "
                    "validate whether it is a correct command, taking into account the files in the project and the syntax of the language being used.\n"
                    "Message: " + myMessage +
                    "\nYour response should follow one of two options:\n"
                    "- Reply 'ParametersToUse' if this message does not contain a valid command.\n"
                    "- If this message contains a valid command that can be run inside a container in TTY mode, your reply should include only the command to be used in Unix-like systems."
            ),

            "contentShort": None
        }

        messagesToChat.append(message1confirmation)
        messagesToChat = convert_json_to_string(messagesToChat)

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            # #model="gpt-4o",
            # model="chatgpt-4o-latest",
            messages=
            messagesToChat,

        )

        messageText = completion.choices[0].message.content
        print(messageText)

        if messageText == "ParametersToUse":
            appendMessage(messagesToUser, contentShort="Please provide a valid command.", stage="ParametersToUse")
        else:
            appendMessage(messagesToUser, content=messageText,
                          contentShort="I will use this command to execute the experiment.\n Command: " + messageText,
                          stage="FindConfigurations")
        return makeResponse(messagesToUser, 201, True)

    except Exception as error:
        print(str(error))
        appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred", stage="Start")
        return makeResponse(messagesToUser, 201, True)


def return_commands_to_use(requestData, messagesToUser):
    if "commandToRun" not in requestData:
        appendMessage(messagesToUser, contentShort="The commandToRun is required", stage="BuildDockerFile")
        return makeResponse(messagesToUser, 201, True)

    commandToRun = requestData["commandToRun"]
    # commandToUse = "make && ./iubfc 13 0.5 ./Data/IMDBID.txt ./Data/IMDBEdge.txt 10000 ./Data/dataOut.txt"
    return commandToRun


@app.route('/project/<projectUuid>/find-configurations', methods=['POST'])
@cross_origin()
def find_configurations(projectUuid):
    directoryPath = 'projects/' + projectUuid + "/files/"
    requestData = json.loads(request.data)
    messagesToUser = []
    messagesToChat = []

    if "filenames" not in requestData:
        appendMessage(messagesToUser, contentShort='filenames are missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    filenames = requestData["filenames"]
    # filenames= ['main.py', 'main2.py', 'main3.py', 'new\\main.py', 'new\\main2.py', 'new\\main3.py', 'new\\newnew\\main2.py', 'new\\newnew\\main3.py']

    commandToRun = return_commands_to_use(requestData, messagesToUser)

    # filenames = ['main.py']
    all_files_lines = {}

    try:
        for filename in filenames:
            if os.path.isfile(directoryPath + filename):
                lines = read_first_50_lines(directoryPath + filename)
                all_files_lines[filename] = lines
            else:
                print(f"File not found: {filename}")
    except Exception as error:
        appendMessage(messagesToUser, contentShort=str(error), stage="Start")
        return makeResponse(messagesToUser, 201, True)

    # Convert the content to JSON format
    filesContent = json.dumps(all_files_lines, indent=4)

    numberInteractions = 3
    chat_message = ""

    try:
        while numberInteractions >= 0:
            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chat_message + "The current stage of this interaction is: FindConfigurations"
                                                  "\nGiven the JSON containing the name of the files, the first 50 lines of each file and the command used to execute this project, determine the following:"
                                                  "\nThe programming language of the files."
                                                  "\nThe version of these languages."
                                                  "\nAny dependencies needed to execute the command and their versions."
                                                  '\nProvide your response in the following format:'
                                                  '{ "PL": [all the programming languages used], "PLVersion": [all the programming language version],"Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                                                  '\nEnsure the dependency names are correct. If the provided name is incorrect, adjust it. For example, in Python, to install the sklearn dependency, the correct command is pip install scikit-learn.'
                                                  '\nMake sure to list the most recent supported version of the programming language, and format the result in JSON.'
                                                  "\nOnly put values that you can infer, don't put generic values"
                                                  '\nCommand To Use: ' + commandToRun +
                                   '\nExample response:'
                                   '\n{ "PL": ["Python"], "PLVersion": "Python 3.8", "Dependencies": ["pandas"], "DependenciesVersion": ["pandas==2.2.0"]}'
                                   '\nPlease respond in the specified format. The answer should be exactly in json format.'

                        }

            messagesToUser.append(message1)
            myMessage = copy(message1)
            myMessage["content"] = myMessage["content"] + '\nThe first 50 lines of each file: ' + str(filesContent)
            messagesToChat.append(myMessage)

            # TODO descomentar
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                # #model="gpt-4o",
                # model="chatgpt-4o-latest",
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
                print("Error:" + str(e))
                messagesToChat = []

                message1 = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "content": chat_message +
                                       "\nExtract from the following message a JSON in the required format."
                                       "\nMessage: " + messageText +
                                       '\nRequired JSON format: '
                                       '{ "PL": [programming language], "PLVersion": [programming language version], "Dependencies": [dependencies], "DependenciesVersion": [version of dependencies] }'
                                       '\nEnsure the response is in the specified JSON format. '
                            }
                messagesToChat.append(message1)

                # TODO descomentar
                client = OpenAI()
                completion = client.chat.completions.create(
                    model="gpt-4-turbo",
                    # model="gpt-4o",
                    # model="chatgpt-4o-latest",
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
                    print("numberInteractions" + str(numberInteractions))
                    chat_message = "The previous result is incorrect. I encountered this error: " + str(e) + \
                                   "\nPlease consider the following information.\n"

    except Exception as error:
        appendMessage(messagesToUser, content="I got this error:" + str(error),
                      contentShort="I got this error:" + str(error), stage="Start")
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
        model="gpt-4-turbo",
        # model="gpt-4o",
        # model="chatgpt-4o-latest",
        messages=
        messagesToChat,

    )
    messageText = completion.choices[0].message.content
    print(messageText)

    if messageText == "BuildDockerFile" or messageText == "WaitChatInteraction":
        appendMessage(messagesToUser, content=messageText, stage=messageText)
        return makeResponse(messagesToUser, 201, True)
    else:
        messageText = messageText.replace("```", "")
        messageText = messageText.replace("json", "")
        try:
            appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True, stage="WaitChatInteraction")
            return makeResponse(messagesToUser, 201, True)
        except Exception as e:
            numberInteractions = 3
            chat_message = ""
            while numberInteractions >= 0:
                message1 = {"role": "system",
                            "jsonObject": False,
                            "contentShort": None,
                            "content": chat_message +
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
                    model="gpt-4-turbo",
                    # model="gpt-4o",
                    # model="chatgpt-4o-latest",
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
                    chat_message = "The previous result is incorrect. Please consider the following information.\n"

        appendMessage(messagesToUser, content="Some error occurred", contentShort="Some error occurred",
                      stage="FindConfigurations")
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
                           "Check if you find this sentence in the conversation history. I tried to build the Docker image, but an error occurred "
                           "If so, you have to take the previous docker file into account so that you don't provide the same dockerfile because the previous one had an error."
                           'Please use the information I have provided, such as the dependencies, their versions (DependenciesVersion), programming languages (PL), and programming language versions (PLVersion), to build a Dockerfile. '
                           'All the files I want to use are located in the files folder. Inside the container, I want all the files to remain in the files folder as well. '
                           'Therefore, the following two commands should be used: '
                           '"WORKDIR /files" and "COPY files/ ."'
                           '\nDo not use any additional COPY commands. '
                           'In previous messages, I provided the names of the configuration files (configurationFiles) present in the project. '
                           'You may use them if relevant, but it’s not necessary to include COPY or ADD commands for these files, because they are inside the "./files" folder and have already been copied. '
                           'Please do not infer the names of any files not explicitly provided. '
                           'I only need the Dockerfile required to build the Docker image, so do not include the CMD or ENTRYPOINT commands in this Dockerfile. '
                           'Provide only the created Dockerfile, as I will use your response directly—no additional text or explanation is needed.'}

    messagesToUser.append(message1)
    messagesToChat.append(message1)
    messagesToChat = convert_json_to_string(messagesToChat)
    # messageText = ''

    # TODO descomentar
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4-turbo",
        # #model="gpt-4o",
        # model="chatgpt-4o-latest",
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
        model="gpt-4-turbo",
        # #model="gpt-4o",
        # model="chatgpt-4o-latest",
        messages=
        messagesToChat,

    )

    messageText = completion.choices[0].message.content
    messageText = messageText.replace("```", "")
    messageText = messageText.replace("Dockerfile", "")
    messageText = messageText.replace("dockerfile", "")

    # TODO comentar
    #     messageText = """FROM python:3.10
    #
    # WORKDIR /files
    # COPY files/ .
    #
    # RUN pip install shap==0.41.0 numpy==1.23.4 pandas==1.5.2 scipy==1.9.3 matplotlib==3.6.2 tqdm==4.64.1"""

    write_file(projectPath + "Dockerfile", messageText)
    try:
        appendMessage(messagesToUser, content=json.loads(messageText), jsonObject=True, stage="BuildDockerImage")
    except Exception as e:
        appendMessage(messagesToUser, content=messageText, stage="BuildDockerImage")
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

    if "nextStep" in requestData:
        nextStep = requestData["nextStep"]
    else:
        appendMessage(messagesToUser, contentShort='NextStep is missing', stage="Start")
        return makeResponse(messagesToUser, 201, True)

    numberInteractions = 3
    chatMessage = ""

    try:
        while numberInteractions >= 0:
            # TODO descomentar
            message1 = {"role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chatMessage + "Please evaluate the following message content: "
                                                 "If the message propose possible changes, reply with 'CHANGE' "
                                                 "If the message is positive or indicates agreement, respond with '" + nextStep +
                                   "'. If the message is negative and indicates disagreement, but does not propose possible changes, respond with 'WaitChatInteraction' "
                                   "\nPlease respond in the specified format. The answer should be exactly one word."
                                   "\nMessage: " + myMessage + ""
                        }
            messagesToUser.append(message1)
            messagesToChat.append(message1)

            messagesToChat = convert_json_to_string(messagesToChat)

            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                # #model="gpt-4o",
                # model="chatgpt-4o-latest",
                messages=
                messagesToChat,

            )
            messageText = completion.choices[0].message.content
            print(messageText)

            palavras = messageText.split()
            if len(palavras) == 1:
                if messageText == "CHANGE":
                    message1 = {
                        "role": "system",
                        "jsonObject": False,
                        "contentShort": None,
                        "content": chatMessage + 'Please evaluate the following message:\n'
                                                 'Reply with "FindConfigurationsInteraction" if the message relates to the configuration '
                                                 'of the computing environment (e.g., dependency versions or missing programming languages).\n'
                                                 'Reply with "ProjectLocation" if the message involves changing the location of the project.\n'
                                                 'Reply with "ParametersToUse" if the message concerns the command used to run a computational experiment.\n'
                                                 '\nPlease respond in the specified format. The answer should be exactly one word.\n'
                                                 'Message: "' + myMessage + '"'
                    }

                    messagesToUser.append(message1)
                    messagesToChat.append(message1)

                    messagesToChat = convert_json_to_string(messagesToChat)

                    client = OpenAI()
                    completion = client.chat.completions.create(
                        model="gpt-4-turbo",
                        # #model="gpt-4o",
                        # model="chatgpt-4o-latest",
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
                chatMessage = "The previous result is incorrect. The answer should be exactly one word. Please consider the following information.\n"
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
        # TODO comentar
        # try:
        #     # Build the image and stream the logs in real-time
        #     dockerImageBuilt = dockerClient.images.build(path=projectPath, tag=projectUuid + ":" + number, rm=True,
        #                                                  stream=True)
        #     # Loop through the logs and print them in real-time
        #     for chunk in dockerImageBuilt:
        #         if 'stream' in chunk:
        #             print(chunk['stream'].strip())  # Print the log messages in real-time
        #         else:
        #             print(chunk)  # Catch other potential messages (like errors)
        # except Exception as e:
        #     raise Exception(str(e))
        dockerImageBuilt = dockerClient.images.build(path=projectPath, tag=projectUuid + ":" + number, rm=True)
        dockerImageBuiltFiltered = [s for s in dockerImageBuilt[0].tags if projectUuid in s]
        dockerTagslength = len(dockerImageBuiltFiltered) - 1

        messageText = dockerImageBuiltFiltered[dockerTagslength]

        # TODO comentar
        # messageText = "e25:20240917151400"
        # raise Exception("gcc: error: -E or -x required when input is from standard input")

        appendMessage(messagesToUser, content=messageText, stage="RunContainer")

        return makeResponse(messagesToUser, 201, True)
    except Exception as e:
        print(str(e))
        dockerfile_content = read_file(projectPath + "Dockerfile")
        message11 = {
            "role": "system",
            "jsonObject": False,
            "contentShort": None,
            "content": 'The stage of this iteration is: BuildDockerImage.\n'
                       'I have this Dockerfile:\n' + dockerfile_content +
                       '\nI tried to build the Docker image, but an error occurred:\n' + str(e) +
                       '\nIs the error due to the Dockerfile? If so, just reply "YES". '
                       'If the problem is not with the Dockerfile, just reply "NO".'
        }
        messagesToChat = []
        messagesToChat.append(message11)

        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            # model="gpt-4o",
            # model="chatgpt-4o-latest",
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
                                         "What might have caused this unexpected result?")
            examples = ("I want to change the execution parameters.\n"
                        "I want to change the project location.\n"
                        "I want to change the computing environment used (programming languages, dependencies).\n"
                        )
            appendMessage(messagesToUser, contentShort=errorMessage, stage="WaitChatInteraction", examples=examples)

        return makeResponse(messagesToUser, 201, True)


@app.route("/project/<projectUuid>/run-container-chat", methods=['POST'])
@cross_origin()
def runDockerContainerChat(projectUuid):
    projectPath = 'projects/' + projectUuid + "/"

    requestData = json.loads(request.data)
    messagesToUser = []

    commandToRun = return_commands_to_use(requestData, messagesToUser)

    if "dockerImageId" in requestData:
        dockerImageId = requestData["dockerImageId"]
    else:
        appendMessage(messagesToUser, contentShort="The dockerImageId is required", stage="BuildDockerFile")
        return makeResponse(messagesToUser, 201, True)

    number_of_attempts = 3

    while number_of_attempts >= 0:
        try:
            dockerClientResult = startDockerClient()
            dockerClient, port = dockerClientResult["dockerClient"], dockerClientResult["port"]

            projectImage = dockerClient.images.get(dockerImageId)
            now = datetime.now()
            number = now.strftime("%Y%m%d%H%M%S")

            current_path = os.getcwd()
            directoryPath = '/projects/' + projectUuid + "/files"

            volume_path = os.path.abspath(current_path + directoryPath)

            # Run the container
            container = dockerClient.containers.run(
                image=projectImage,
                name=projectUuid + "_" + number,
                volumes={volume_path: {'bind': '/files', 'mode': 'rw'}},  # Linux absolute path and bind
                detach=True,
                command="/bin/sh",
                tty=True
            )
            # stdin=True: Allows you to pass input to the container via standard input.
            # You often use both together when running fully interactive sessions in containers. For example:
            # container.exec_run('/bin/bash', stdin=True, tty=True)

            # commandToRun= "python ./myfile.py && cd pasta && python ./myfile2.py && cd .. &&  python ./myfile3.py"
            exec_first = container.exec_run('/bin/sh -c "' + commandToRun + '"')

            containerLogs = "Command Output:" + exec_first.output.decode('utf-8') + "\n\n"
            exit_code = f"Exit Code: {exec_first.exit_code}\n"
            containerLogs += exit_code

            print(containerLogs)

            container.stop()
            # container.remove()

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

            if exec_first.exit_code != 0:
                # if True:
                errorMessage = (
                        "An error occurred during the environment build. \n"
                        + containerLogs +
                        "What might have caused this unexpected result?.")
                examples = ("I want to change the execution parameters.\n"
                            "I want to change the project location.\n"
                            "I want to change the computing environment used (programming languages, dependencies).\n"
                            )

                appendMessage(messagesToUser, contentShort=errorMessage, stage="WaitChatInteraction", examples=examples)
            else:
                messagesToUser = [
                    {"role": "assistant",
                     "content": containerLogs,
                     "contentShort": containerLogs,
                     "jsonObject": False,
                     }

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
            message11 = {
                "role": "system",
                "jsonObject": False,
                "contentShort": None,
                "content": 'The stage of this iteration is: RunContainer.\n'
                           'I have this Dockerfile:\n' + dockerfile_content +
                           '\nI built the Docker image, and the build was successful. '
                           'I used the following command to execute this container: ' + commandToRun +
                           '\nHowever, an error occurred during the execution of the container: ' + str(e) +
                           '\n\nConsider the following error and classify it according to its origin:'
                           '\n- If the problem stems from the construction of the computing environment, such as the version of the dependencies used or the absence of a programming language, then only answer "FindConfigurations".'
                           '\n- If the problem stems from negligence in writing the code, such as errors due to missing files or failing to import functions, then only answer "ProjectLocation".'
                           '\n- If the problem stems from the command used to run the computational experiment, then only answer "ParametersToUse".'
                           '\n\nPlease answer in the required format. The answer should be one word in length.'
            }

            messagesToChat = []
            messagesToChat.append(message11)

            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4-turbo",
                # model="gpt-4o",
                # model="chatgpt-4o-latest",
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

    commandToRun = return_commands_to_use(requestData, messagesToUser)

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
    ##todo precisa de um try
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
    # Initialize the Docker client
    # client = docker.from_env()
    #
    # # Get all running containers
    # containers = client.containers.list()
    #
    # # Print details of each container
    # for container in containers:
    #     print(f"Container ID: {container.id}")
    #     print(f"Image: {container.image.tags}")
    #     print(f"Name: {container.name}")
    #     print(f"Status: {container.status}")
    #     print(f"Ports: {container.attrs['NetworkSettings']['Ports']}")
    #     print("-" * 40)

    # TODO é necssario escrever FLASK_RUN_PORT=8080 nas variaveis de ambiente da execução para a porta a executar ser a correta
    app.run(host='0.0.0.0', port=8080)

    # TODO Correr experiencias com interface grafica
    # Não é necesario ter export no dockerfile, o container tem que ser corrido desta maneira
    # dockerClient.containers.run(image="web:2",  ports={4200:4200}, command="npm run start", name = "ola" + "_" + "4200", detach = True)
    #

    # dockerClientResult = startDockerClient()
    # dockerClient, port = dockerClientResult["dockerClient"], dockerClientResult["port"]
    # number = datetime.now().strftime("%Y%m%d%H%M%S")
    # projectUuid = "iubfc_main"
    # projectPath = 'projects/' + projectUuid + "/"
    #
    # dockerImageBuilt = dockerClient.images.build(path=projectPath, tag=projectUuid + ":" + number, rm=True)
    # dockerImageBuiltFiltered = [s for s in dockerImageBuilt[0].tags if projectUuid in s]
    # dockerTagslength = len(dockerImageBuiltFiltered) - 1
    #
    # projectImage = dockerImageBuiltFiltered[dockerTagslength]
    #
    # # projectImage ="iubfc_main:20240922185634"
    #
    # # Use an absolute path for the volume
    # # Replace '/home/youruser' with the appropriate path where your project is stored on Linux
    # current_path = os.getcwd()
    # directoryPath = '/projects/' + projectUuid + "/files"
    #
    # volume_path = os.path.abspath(current_path + directoryPath)
    #
    # # Run the container
    # container = dockerClient.containers.run(
    #     image=projectImage,
    #     name=projectUuid + "_" + number,
    #     volumes={volume_path: {'bind': '/files', 'mode': 'rw'}},  # Linux absolute path and bind
    #     detach=True,
    #     command="/bin/sh",
    #     tty=True
    # )
    # #commandToRun = "make && ./iubfc 13 0.5 ./Data/IMDBID.txt ./Data/IMDBEdge.txt 10000 ./Data/dataOut.txt"
    # commandToRun = "make"
    #
    # exec_first = container.exec_run('/bin/sh -c "' + commandToRun + '"')
    #
    # containerLogs = "Command Output:" + exec_first.output.decode('utf-8') + "\n\n\n"
    # exit_code = f"Exit Code: {exec_first.exit_code}\n"
    # containerLogs += exit_code
    #
    # print(containerLogs)
    #
    # container.stop()
