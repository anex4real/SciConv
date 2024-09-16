import os
import tarfile
import uuid
import re
import zlib

requestConfig = {
    "headers": {
        "Accept": "application/zip",
    },
    "responseType": "arraybuffer",
}
requestConfigAcceptAll = {
    "headers": {
        "Accept": "*/*",
    },
    "responseType": "arraybuffer",
}


def getProjectDirectory(projectUuid):
    current_directory = os.getcwd()
    print("Current working directory: {0}".format(current_directory))
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    projectDirectory = parent_directory + "/repositories"

    if not os.path.exists(projectDirectory):
        os.makedirs(projectDirectory)

    myProjectFolder = projectDirectory + "/" + projectUuid
    if not os.path.exists(myProjectFolder):
        os.makedirs(myProjectFolder)

    return myProjectFolder


def getProjectLocation(projectUuid):
    current_directory = os.getcwd()
    print("Current working directory: {0}".format(current_directory))

    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    print(parent_directory)

    myProjectFolder = getProjectDirectory(projectUuid)
    projectFiles = myProjectFolder + "/files"

    return {"projectFiles": projectFiles, "myProjectFolder": myProjectFolder}


def get_all_file_paths(directory):
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths


def find_files(directory):
    files = []
    directory = os.path.abspath(directory)  # Convert to absolute path for consistency

    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)

            # Remove the directory prefix from the full path
            reduced_path = os.path.relpath(full_path, directory)

            files.append(reduced_path)

    return files
    # files = []
    # base_dir = os.path.basename(directory.rstrip(os.sep))  # Get the base directory name
    #
    # for root, dirs, filenames in os.walk(directory):
    #     for filename in filenames:
    #         full_path = os.path.join(root, filename)
    #
    #         # Compute the relative path and prepend the base directory
    #         rel_path = os.path.relpath(full_path, directory)
    #         reduced_path = os.path.join(base_dir, rel_path)
    #
    #         files.append(reduced_path)
    #
    # return files


def read_first_50_lines(file_path):
    """Reads the first 50 lines of a file and returns them while preserving indentation."""
    lines = []
    try:
        with open(file_path, 'r') as file:
            for i in range(50):
                line = file.readline()
                if not line:
                    break
                lines.append(line.rstrip())  # Preserve the indentation
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return lines

#
# from project import (addFilesToDatabase, createProject, getProject, getAllProjects, getPythonFilesByProjectDatabase,
#                      getFilesByProjectDatabase, getFoldersFromFolderDatabase, getFilesFromFolderDatabase,
#                      addFoldersToDatabase, getFoldersByProjectDatabase, deleteProject, addLanguagesToProjectDatabase,
#                      getLanguagesFromProject)
# from config.neo4j import initializeSession
#
# myArgs = sys.argv[1:]
# env = myArgs[0] if myArgs else None
# config = __import__(f"config.{env}", fromlist=["config"]).config
#
#
#
# def make_folder_root(project_uuid):
#     repositories_directory = "./repositories"
#     if not os.path.exists(repositories_directory):
#         os.mkdir(repositories_directory)
#
#     project_directory = os.path.join(repositories_directory, project_uuid)
#     if not os.path.exists(project_directory):
#         os.mkdir(project_directory)
#
#     project_files = os.path.join(project_directory, "files")
#     if not os.path.exists(project_files):
#         os.mkdir(project_files)
#
#     # --------------------
#     extracted_directory = "./extracted"
#     if not os.path.exists(extracted_directory):
#         os.mkdir(extracted_directory)
#
#     extracted_project_directory = os.path.join(extracted_directory, project_uuid)
#     if not os.path.exists(extracted_project_directory):
#         os.mkdir(extracted_project_directory)
#
#     return project_files
#
# # see https://docs.figshare.com/
# # figshare
# # get all the information from a project curl -X GET "https://api.figshare.com/v2/articles/{article_id}"
# # https://docs.figshare.com/#public_article
# #
# #
# # download all the files from a project
# # https://figshare.com/ndownloader/articles/20965759/versions/1 ---zipfile
# # https://figshare.com/ndownloader/articles/<figshare doi>/versions/<version 1..*>
# #
# # get all the files from a project
# # https://api.figshare.com/v2/articles/20965759/files ---list
# # https://api.figshare.com/v2/articles/<doi>/files
# # https://docs.figshare.com/#article_files
# #
# #
# # https://zenodo.org/record/51908#.ZAj0WXbP1D-
# # 10.5281/zenodo.51908
# #
# # figshare
# # https://figshare.com/articles/journal_contribution/Summarizing_Data_in_Python_with_Pandas/1041843
# # https://doi.org/10.6084/m9.figshare.1041843.v3
#
# import aiohttp
# import asyncio
# import os
#
#
# async def getProjectFromRemoteRepository(projectUuid, projectFiles, bodyRequest):
#     defaultBranchName = bodyRequest["defaultBranchName"]
#     projectLocation = bodyRequest["projectLocation"]
#     repositorySelected = bodyRequest["repositorySelected"]
#     requestResultArray = []
#
#     hasZipFile = False;
#
#     async with aiohttp.ClientSession() as session:
#         if repositorySelected == "GitHub":
#             async with session.get(f"https://github.com/{projectLocation}/archive/refs/heads/{defaultBranchName}.zip") as response:
#                 requestResultArray.append(await response.read())
#         elif repositorySelected == "Figshare":
#             regexpSize = r'(?:[a-z]|\.|:|\/)*10.6084\/m9.figshare.([0-9]+).v([0-9]+)'
#             match = re.search(regexpSize, projectLocation)
#             if not match or len(match.groups()) != 2:
#                 return None
#             else:
#                 async with session.get(f"https://figshare.com/ndownloader/articles/{match.group(1)}/versions/{match.group(2)}") as response:
#                     requestResultArray.append(await response.read())
#         elif repositorySelected == "Zenodo":
#             regexpSize = r'(?:[a-z]|\.|:|\/)*10.5281\/zenodo.([0-9]+)'
#             match = re.search(regexpSize, projectLocation)
#             if not match or len(match.groups()) != 1:
#                 return None
#             else:
#                 async with session.get(f"https://zenodo.org/api/records/{match.group(1)}") as response:
#                     result = await response.json()
#                     for file in result["files"]:
#                         downloadAllFiles = bodyRequest.get("downloadAllFiles", False)
#                         filesToDownloads = bodyRequest.get("files", [])
#
#                         downloadThisFile = True
#
#                         if not downloadAllFiles:
#                             if not isinstance(filesToDownloads, list):
#                                 return []
#                             if file["filename"] not in filesToDownloads:
#                                 downloadThisFile = False
#                         if downloadThisFile:
#                             async with session.get(file["links"]["download"]) as resultfile:
#                                 if resultfile.headers["content-type"] == "application/zip" or resultfile.headers["content-type"] == "application/octet-stream":
#                                     requestResultArray.append({
#                                         "data": await resultfile.read(),
#                                         "filename": file["filename"]
#                                     })
#                                     hasZipFile = True
#                                 else:
#                                     with open(f"{projectFiles}/{file['filename']}", "wb") as f:
#                                         f.write(await resultfile.read())
#
#         if repositorySelected == "Zenodo" and not hasZipFile:
#             return False
#         else:
#             filenameArray = []
#             for zipFile in requestResultArray:
#                 filenameArray.append(zipFile["filename"])
#                 os.makedirs(f"./extracted/{projectUuid}", exist_ok=True)
#                 with open(f"./extracted/{projectUuid}/{zipFile['filename']}", "wb") as f:
#                     f.write(zipFile["data"])
#             return filenameArray
#
# import tarfile
# import zlib
# import os
#
# async def openAndExtractGZFile(projectUuid, projectFiles, fileOrProject):
#     compressedContents = open(f"./extracted/{projectUuid}/{fileOrProject.name}", "rb").read()
#     extractedContents = zlib.decompress(compressedContents)
#     extractPath = os.path.join(projectFiles, fileOrProject.name)
#     with open(extractPath, "wb") as extractedFile:
#         extractedFile.write(extractedContents)
#     os.unlink(f"./extracted/{projectUuid}/{fileOrProject.name}")
#
#
# async def openAndExtractZipFile(projectUuid, projectFiles, fileOrProject):
#     zip
#     #zip = await StreamZip.async({"file": f"./extracted/{projectUuid}/{fileOrProject.name}"})
#     entries = await zip.entries()
#     allEntities = []
#     for entry in entries.values():
#         rootEntity = entry.name.split("/")[0]
#         allEntities.append(rootEntity)
#     allEntitiesWithoutDuplicates = list(set(allEntities))
#     if len(allEntitiesWithoutDuplicates) == 1:
#         await zip.extract(allEntitiesWithoutDuplicates[0], path=projectFiles)
#     else:
#         await zip.extractall(path=projectFiles)
#     os.unlink(f"./extracted/{projectUuid}/{fileOrProject.name}")
#     await zip.close()
#
#
# async def addFilesAndFolderToProjectAux(extractedFolder, projectUuid, firstIteration, parentDirectoryKey, fileExtention):
#     filesToAdd = []
#     foldersToAdd = []
#     if not firstIteration:
#         print("aqui")
#
#     # list all files in the directory
#     try:
#         files = os.listdir(extractedFolder)
#         for file in files:
#             if not file.endswith(".zip"):
#                 stats = os.stat(extractedFolder + '/' + file)
#                 print("full path")
#                 fullPath = extractedFolder + '/' + file
#                 fullPathSplited = fullPath.split("./extracted/" + projectUuid + "/")
#                 print("stats")
#
#                 if os.path.isfile(fullPath):
#                     fileInformation = {
#                         'name': file,
#                         'size': stats.st_size,
#                         'key': str(uuid4()),
#                         'fullPath': fullPathSplited[1],
#                         'dateModified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     }
#                     myFileExtentionArray = file.split(".")
#                     if len(myFileExtentionArray) > 1:
#                         fileExtention.append(myFileExtentionArray[1])
#                     filesToAdd.append(fileInformation)
#
#                 elif os.path.isdir(fullPath) and file != ".idea" and file != "__pycache__":
#                     folderInformation = {
#                         'name': file,
#                         'key': str(uuid4()),
#                         'fullPath': fullPathSplited[1],
#                         'dateModified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     }
#                     foldersToAdd.append(folderInformation)
#
#         session = initializeSession()
#
#         if len(filesToAdd) > 0:
#             if firstIteration:
#                 result = await addFilesToDatabase(session, projectUuid, filesToAdd)
#             else:
#                 result = await addFilesToDatabase(session, projectUuid, filesToAdd, parentDirectoryKey)
#
#             if len(result.records) == 0:
#                 await session.rollback()
#                 return False
#             else:
#                 await session.commit()
#                 await session.close()
#
#         if len(foldersToAdd) > 0:
#             session = initializeSession()
#             if firstIteration:
#                 print("_______________________")
#                 result = await addFoldersToDatabase(session, projectUuid, foldersToAdd)
#             else:
#                 result = await addFoldersToDatabase(session, projectUuid, foldersToAdd, parentDirectoryKey)
#
#             if len(result.records) == 0:
#                 await session.rollback()
#                 return False
#             else:
#                 await session.commit()
#                 await session.close()
#
#                 for folderCreated in result.records[0]._fields:
#                     myFolderInformation = folderCreated.properties
#
#                     myResult = await addFilesAndFolderToProjectAux(extractedFolder + '/' + folderCreated.properties['name'], projectUuid, False, myFolderInformation, fileExtention)
#                     if not myResult:
#                         return False
#
#         return True
#     except Exception as e:
#         print(e)
#         return False
#
#
# #import asyncio
# #from datetime import datetime
# #from database_operations import initialize_session, get_folders_by_project_database, get_files_by_project_database, get_folders_from_folder_database, get_files_from_folder_database
#
#
# async def get_content_from_folder_aux(project_uuid, key, first_iteration):
#     print("key: " + key)
#     try:
#         date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         print(date)
#         items = []
#         session = initialize_session()
#         if first_iteration:
#             my_result = await get_folders_by_project_database(session, project_uuid)
#             my_result2 = await get_files_by_project_database(session, project_uuid)
#             date2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             print(date2)
#             my_result.records += my_result2.records
#         else:
#             my_result = await get_folders_from_folder_database(session, key)
#             my_result2 = await get_files_from_folder_database(session, key)
#             my_result.records += my_result2.records
#         await session.close()
#         date3 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         print(date3)
#
#         if len(my_result.records) == 0:
#             return []
#         else:
#             for record in my_result.records:
#                 for field in record._fields:
#                     if field is not None:
#                         node_type = field.labels[0]
#                         if node_type == "Folder":
#                             print("ciclo")
#                             result_object = await get_content_from_folder_aux(None, field.properties["key"], False)
#
#                             folder_result = field.properties
#                             folder_result["isDirectory"] = True
#                             folder_result["items"] = result_object
#
#                             items.append(folder_result)
#                         if node_type == "File":
#                             file_result = field.properties
#                             file_result["isDirectory"] = False
#                             items.append(file_result)
#         return items
#     except Exception as e:
#         raise e
