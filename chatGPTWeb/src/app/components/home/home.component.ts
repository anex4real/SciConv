import {Component, OnInit} from '@angular/core';
import {DomSanitizer} from "@angular/platform-browser";
import {BackendService} from "../../service";
import {Message} from "../../interface/interfaces";
import {BehaviorSubject} from 'rxjs';

enum Stage {
    Start = 'Start',
    ProjectLocation = 'ProjectLocation',
    FindProjectFiles = 'FindProjectFiles',


    ParametersToUse = 'ParametersToUse',

    FindConfigurations = 'FindConfigurations',
    FindConfigurationsInteraction = 'FindConfigurationsInteraction',
    BuildDockerFile = 'BuildDockerFile',
    BuildDockerImage = 'BuildDockerImage',
    RunContainer = 'RunContainer',
    ResearchArtifact = 'ResearchArtifact',

    WaitChatInteraction = 'WaitChatInteraction',

    Completed = 'Completed'
}

@Component({
    selector: 'app-home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.css', '../../app.component.css']
})
export class HomeComponent implements OnInit {
    protected readonly Array = Array;
    private fileToUpload: File | null = null;
    password: string = '';
    isAuthenticated: boolean = true;

    stages = Stage; // Expose the enum to the template
    stageSubject = new BehaviorSubject<Stage>(Stage.Start); // Default to Initial stage
    currentStage$ = this.stageSubject.asObservable(); // Observable to track the current stage
    role: string = 'system'; // You can make this dynamic as needed
    stageAfterChat: any

    userMessage = '';
    configurations: any
    messages: Message[] = [];
    executableFiles: any
    configurationFiles: object = {}
    dockerImageID: any;
    //todo remover conteudo
    projectUuid: string = ""
    //projectUuid: string = 'ads_main';
    //projectUuid: string = "iubfc_main"
    commandToRun = ""
    //commandToRun = "python ./yahoo_demo.py\n"
    //commandToRun: string = "python ./myfile.py";
    //commandToRun: string = "make"
    //commandToRun: string = "make && ./iubfc 13 0.5 ./Data/IMDBID.txt ./Data/IMDBEdge.txt 10000 ./Data/dataOut.txt"

    logs: any;
    added_files: any;
    removed_files: any;
    modified_files: any;
    messageToAsk: any;
    examplesToAsk: any = undefined
    errorMessage: any;
    GOBACKNUMBER: any = 3;
    goBack: any
    isLoading: boolean = false


    constructor(private sanitizer: DomSanitizer, protected backend: BackendService) {
        this.goBack = this.GOBACKNUMBER
    }

    ngOnInit(): void {
        this.currentStage$.subscribe((newStage) => {
            console.log(`Stage changed to ${newStage}`);
            this.performActionBasedOnStage(newStage);
        });
    }

    examplesVisibility: { [key: string]: boolean } = {};

    toggleExamples(message: any): void {
        const messageId = message.id || message.contentShort;
        this.examplesVisibility[messageId] = !this.examplesVisibility[messageId];
    }

    isExamplesVisible(message: any): boolean {
        const messageId = message.id || message.contentShort;
        return !!this.examplesVisibility[messageId];
    }

    changeStage(newStage: Stage): void {
        this.stageSubject.next(newStage);
    }

    private performActionBasedOnStage(stage: Stage): void {
        switch (stage) {
            case Stage.Start:
                console.log('Action for Initial stage');
                break;
            case Stage.ProjectLocation:
                this.projectLocation()
                break;
            case Stage.FindProjectFiles:
                this.findProjectFiles()
                break;
            // case Stage.FileToRun:
            //     this.fileToRun()
            //     break;
            case Stage.ParametersToUse:
                this.parametersToUseFunc()
                break;
            case Stage.FindConfigurations:
                this.findConfigurations()
                break
            case Stage.FindConfigurationsInteraction:
                this.findConfigurationsInteraction()
                break
            case Stage.WaitChatInteraction:
                this.waitChatInteraction(this.messageToAsk)
                break
            case Stage.BuildDockerFile:
                this.buildDockerFile()
                break
            case Stage.BuildDockerImage:
                this.buildDockerImage()
                break
            case Stage.RunContainer:
                this.runContainer()
                break
            case Stage.ResearchArtifact:
                this.researchArtifact()
                break
            case Stage.Completed:
                console.log('Action for Completed stage');
                break;
            default:
                console.log('Unknown stage');
        }
    }

    objectKeys(obj: any): string[] {
        return Object.keys(obj);
    }

    isObject(value: any): boolean {
        return value && typeof value === 'object' && !Array.isArray(value);
    }

    sendMessage() {
        this.messages.push({
            role: this.role,
            contentShort: this.userMessage,
            content: this.userMessage,
            jsonObject: false,
        });
        switch (this.stageSubject.value) {
            case Stage.ProjectLocation:
                this.projectUuid = this.userMessage
                this.changeStage(this.stages.FindProjectFiles)
                break;
            case Stage.ParametersToUse:
                this.parametersToUseConfirmation()
                break;
            case Stage.WaitChatInteraction:
                this.chatInteraction()
                break;
            case Stage.FindConfigurationsInteraction:
                this.findConfigurationsFunc(this.userMessage)
                break;
            case Stage.Completed:
                this.changeStage(this.stages.ResearchArtifact)
                break;
            default:
                console.log('Unknown stage');
        }
        this.userMessage = '';
    }

    projectLocation() {
        this.messages.push({
            role: "assistant",
            content: "Please provide the location of the project.",
            contentShort: "Please provide the location of the project.",
            jsonObject: false,
            examples: "This refers to the root folder or directory where the main files of your project are stored. Having the root folder clearly specified helps in organizing files, ensuring that all paths are correctly referenced, and simplifies collaboration with others.\n" +
                "\nExamples: \nYou can provide a sentence e.g. 'The root folder of the project is located at example_folder_name'\n" +
                "You can only provide the folder name, e.g., 'example_folder_name'"
        });


        this.userMessage = this.projectUuid
        //this.sendMessage()
    }

    findProjectFiles() {
        this.isLoading = true;

        this.backend.findProjectFiles(this.projectUuid).subscribe({
            next: (response: any) => {
                this.isLoading = false;
                this.messages.push(...response);
                const responseLength = response.length;

                if (response[responseLength - 1].stage === "ParametersToUse") {
                    console.log(response[responseLength - 1]["content"]);
                    const { ExecutableFiles, ConfigurationFiles, ProjectUuid } = response[responseLength - 1]["content"];
                    this.executableFiles = ExecutableFiles;
                    this.configurationFiles = ConfigurationFiles;
                    this.projectUuid = ProjectUuid;

                    console.log('Configuration Files:', this.configurationFiles);
                    console.log('Executable Files:', this.executableFiles);
                }

                if (this.executableFiles?.length === 1) {
                    // Optional logic if only 1 executable file
                }

                this.changeStage(response[responseLength - 1].stage);
            },
            error: (err) => {
                console.error("Error fetching project files:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to find project files. Please check your connection or authentication.";
            }
        });
    }





    parametersToUseFunc() {
        this.messages.push({
            role: "assistant",
            content: "Feel free to update any previous information. For example: I want to change the project location to exp26.\n"
                + "Enter the commands needed to run the experiment Note that I'm going to run all the commands sequentially. " +
                "\nFor example: python ./myfile.py && cd folder && python ./myfile2.py && cd .. && python ./myfile3.py",
            contentShort: "Please provide the commands required to run the experiment, keeping in mind that I will execute them sequentially.",
            jsonObject: false,
            examples: "Make sure they are in the correct order to avoid any errors.\n" +
                "\nExamples: \nYou can provide a single command e.g., python ./main.py\n" +
                "You can provide a sequence of commands, e.g., python ./myfile.py && cd folder && python ./myfile2.py "
        });

        this.userMessage = this.commandToRun
    }

    parametersToUseConfirmation() {
        this.isLoading = true;

        this.backend.parametersToUseConfirmation(this.projectUuid, this.messages).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                this.messages.push(...response);
                const responseLength = response.length;

                if (response[responseLength - 1].stage) {
                    if (response[responseLength - 1].stage === "ParametersToUse") {
                        console.log("ParametersToUse");
                        // this.projectUuid = response[responseLength - 1].content;
                    } else if (response[responseLength - 1].stage === "FindConfigurations") {
                        this.commandToRun = response[responseLength - 1].content;
                    }

                    this.changeStage(response[responseLength - 1].stage);
                }
            },
            error: (err) => {
                console.error("Error in parametersToUseConfirmation:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to confirm parameters. Please check your input or authentication.";
            }
        });
    }


    findConfigurations() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now infer all the necessary information to build the environment, which can take some time.",
            jsonObject: false
        });

        this.isLoading = true;

        this.backend.findConfigurations(this.projectUuid, this.executableFiles, this.commandToRun).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log(response);
                this.messages.push(...response);

                const responseLength = response.length;
                this.configurations = response[responseLength - 1].content;

                if (response[responseLength - 1].stage) {
                    this.changeStage(response[responseLength - 1].stage);
                }
            },
            error: (err) => {
                console.error("Error in findConfigurations:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to infer environment configuration. Please try again.";
            }
        });
    }


    findConfigurationsInteraction() {
        this.messages.push({
            role: "assistant",
            content: "I used these settings. Are they correct, or would you like to change anything? \n" +
                JSON.stringify(this.configurations),
            contentShort: "I used these settings. Are they correct, or would you like to change anything? \n" +
                JSON.stringify(this.configurations),
            jsonObject: false,
            examples: "Change the version of the programming version to 3.8.\n" +
                "Change the version of the pandas dependency to 2.2.2.\n"
                + "Remove the dependency pandas.\n"
                + "Remove the programming language c++.\n"
                + "Add the programming language c++.\n"
                + "Add the dependency pandas.\n"
                + "I want to use this configuration networkx==2.5 scikit-learn==0.23.2 tqdm==4.49.0 and python version 3.8"
        });

    }

    findConfigurationsFunc(userMessage: any) {
        this.isLoading = true;

        const myMessage = "Here are the configuration used: " +
            JSON.stringify(this.configurations) +
            "The question is: Are they correct, or would you like to change anything? \n" +
            "The user action is: " + userMessage;

        this.backend.findConfigurationsFunc(this.projectUuid, this.messages, myMessage).subscribe({
            next: (response: any) => {
                this.isLoading = false;
                console.log(response);
                this.messages.push(...response);

                const responseLength = response.length;

                if (response[responseLength - 1].stage === "WaitChatInteraction") {
                    if (response[responseLength - 1].jsonObject === true) {
                        this.configurations = response[responseLength - 1].content;
                    }

                    this.examplesToAsk = "I want to change the execution parameters.\n" +
                        "I want to change the project location.\n" +
                        "I want to change the computing environment used (programming languages, dependencies).\n";

                    this.messageToAsk = "I used these settings. Are they correct, or would you like to change anything? \n" +
                        JSON.stringify(this.configurations);

                    this.stageAfterChat = this.stages.BuildDockerFile;
                }

                this.changeStage(response[responseLength - 1].stage);
            },
            error: (err) => {
                console.error("Error in findConfigurationsFunc:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to process configuration changes. Please try again.";
            }
        });
    }


    buildDockerFile() {
        this.isLoading = true;

        this.backend.BuildDockerFile(this.projectUuid, this.messages).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log(response);
                this.messages.push(...response);
                const responseLength = response.length;

                if (response[responseLength - 1].stage) {
                    this.changeStage(response[responseLength - 1].stage);
                }
            },
            error: (err) => {
                console.error("Error in buildDockerFile:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to build Dockerfile. Please try again.";
            }
        });
    }


    buildDockerImage() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now build the environment to run the experiment, which can take some time.",
            jsonObject: false
        });

        this.isLoading = true;

        this.backend.BuildDockerImage(this.projectUuid, this.messages).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log(response);
                this.messages.push(...response);
                const responseLength = response.length;

                if (response[responseLength - 1].goBack) {
                    console.log("goback");
                    this.goBack -= 1;

                    if (this.goBack <= 0) {
                        this.changeStage(this.stages.FindConfigurationsInteraction);
                        this.goBack = this.GOBACKNUMBER;
                    } else {
                        this.auxFunction(response, responseLength);
                    }
                } else {
                    this.auxFunction(response, responseLength);
                }
            },
            error: (err) => {
                console.error("Error in buildDockerImage:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to build Docker image. Please verify the Dockerfile or environment.";
            }
        });
    }


    auxFunction(response: any, responseLength: any) {
        if (response[responseLength - 1].stage == "RunContainer") {
            this.dockerImageID = response[responseLength - 1]["content"];
            console.log(this.dockerImageID)
        } else if (response[responseLength - 1].stage == "WaitChatInteraction") {
            this.messageToAsk = undefined
            this.stageAfterChat = this.stages.FindConfigurations
        }
        this.changeStage(response[responseLength - 1].stage)
    }

    runContainer() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now run the experiment and provide you with the results as soon as possible.",
            jsonObject: false
        });

        console.log("Command to run:", this.commandToRun);
        this.isLoading = true;

        this.backend.RunContainer(this.projectUuid, this.dockerImageID, this.commandToRun, this.messages).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log(response);
                this.messages.push(...response);
                const responseLength = response.length;

                if (!response[responseLength - 1].stage) {
                    const { logs, added_files, removed_files, modified_files } = response[responseLength - 1]["content"];
                    this.logs = logs;
                    this.added_files = added_files;
                    this.removed_files = removed_files;
                    this.modified_files = modified_files;

                    this.messageToAsk = "Can you confirm whether the result of the execution is correct? " +
                        "\nPlease respond by either confirming or identifying what might have caused this unexpected result and proposing a solution.\n";
                    this.stageAfterChat = this.stages.ResearchArtifact;
                    this.changeStage(this.stages.WaitChatInteraction);
                } else {
                    this.messageToAsk = undefined;
                    this.changeStage(response[responseLength - 1].stage);
                }
            },
            error: (err) => {
                console.error("Error in runContainer:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to run container. Please review the command or image and try again.";
            }
        });
    }


    researchArtifact() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now package all the experiment results into a zip folder and provide you with the result as soon as possible.\n",
            jsonObject: false
        });

        this.isLoading = true;

        this.backend.ResearchArtifact(this.projectUuid, this.dockerImageID, this.commandToRun, this.messages).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log("response");
                console.log(response);
                this.messages.push(...response);
                const responseLength = response.length;
                this.changeStage(response[responseLength - 1].stage);
            },
            error: (err) => {
                console.error("Error in researchArtifact:", err);
                this.isLoading = false;
                this.errorMessage = "Failed to generate the research artifact. Please try again.";
            }
        });
    }


    waitChatInteraction(messageToAsk: any) {
        console.log("aqui")

        if (messageToAsk != undefined) {
            let message

            if (this.examplesToAsk != undefined) {

                message = {
                    role: "assistant",
                    content: messageToAsk,
                    contentShort: messageToAsk,
                    jsonObject: false,
                    examples: this.examplesToAsk
                }
                this.examplesToAsk = undefined;
            } else {
                message = {
                    role: "assistant",
                    content: messageToAsk,
                    contentShort: messageToAsk,
                    jsonObject: false
                }
            }

            this.messages.push(message);
        }
    }

    chatInteraction() {
        if (this.stageAfterChat == undefined) {
            console.error("forcei mudança");
            this.stageAfterChat = this.stages.FindConfigurationsInteraction;
        }

        this.isLoading = true;

        this.backend.ChatInteraction(this.projectUuid, this.messages, this.stageAfterChat).subscribe({
            next: (response: any) => {
                this.isLoading = false;

                console.log(response);
                this.messages.push(...response);
                const responseLength = response.length;

                if (response[responseLength - 1].stage === this.stages.WaitChatInteraction) {
                    this.messageToAsk = "What might have caused this unexpected result? \n";
                    this.examplesToAsk = "I want to change the execution parameters.\n" +
                        "I want to change the project location.\n" +
                        "I want to change the computing environment used (programming languages, dependencies).\n";
                }

                this.changeStage(response[responseLength - 1].stage);
            },
            error: (err) => {
                console.error("Error in chatInteraction:", err);
                this.isLoading = false;
                this.errorMessage = "Chat interaction failed. Please try again.";
            }
        });
    }



    onFileChange(event: any) {
        const file = event.target.files[0];

        if (!file) {
            this.fileToUpload = null;
            return;
        }
        this.fileToUpload = file;
        console.log('Accepted file:', file.name);
    }

    onSubmit() {
        if (this.fileToUpload) {
            const formData = new FormData();
            formData.append('file', this.fileToUpload);

            this.isLoading = true;
            this.backend.uploadProject(formData).subscribe({
                next: (response: any) => {
                    this.isLoading = false;

                    console.log("response");
                    console.log(response);
                    let responseLength = response.length;
                    if (response[responseLength - 1].stage == "FindProjectFiles") {
                        this.projectUuid = response[responseLength - 1].content;
                        this.changeStage(response[responseLength - 1].stage);
                    } else if (response[responseLength - 1].stage) {
                        this.changeStage(response[responseLength - 1].stage);
                        this.messages.push(...response);
                    }
                },
                error: (err) => {
                    console.error("Upload failed:", err);
                    this.isLoading = false;  // 👈 this ensures the button is re-enabled
                    this.errorMessage = "Upload failed. Please check your connection or authentication.";
                }
            });
        }
    }

    onSubmitpass() {
        if (this.backend.validatePassword(this.password)) {
            this.isAuthenticated = true;
            this.errorMessage = '';
        } else {
            this.errorMessage = 'Invalid password. Please try again.';
        }
    }
}