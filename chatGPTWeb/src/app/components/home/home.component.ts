import {Component, OnInit} from '@angular/core';
import {DomSanitizer} from "@angular/platform-browser";
import {BackendService} from "../../service";
import {HttpClient} from '@angular/common/http';
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

    stages = Stage; // Expose the enum to the template
    stageSubject = new BehaviorSubject<Stage>(Stage.Start); // Default to Initial stage
    currentStage$ = this.stageSubject.asObservable(); // Observable to track the current stage
    role: string = 'system'; // You can make this dynamic as needed
    projectUuid: string = 'e25';
    stageAfterChat: any
    stageCurrentChat: any

    userMessage = '';
    configurations: any
    messages: Message[] = [];
    executableFiles: any
    configurationFiles: object = {}
    dockerImageID: any;
    commandToRun: string = "python ./myfile.py";

    logs: any;
    added_files: any;
    removed_files: any;
    modified_files: any;
    messageToAsk: any;
    showInfo: boolean = false


    constructor(private sanitizer: DomSanitizer,
                protected backend: BackendService, private http: HttpClient
    ) {
    }

    ngOnInit(): void {
        // Subscribe to stage changes
        this.currentStage$.subscribe((newStage) => {
            console.log(`Stage changed to ${newStage}`);
            this.performActionBasedOnStage(newStage);
        });
    }

    // Method to change the stage
    changeStage(newStage: Stage): void {
        this.stageSubject.next(newStage);
    }


    // Perform an action based on the stage
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

    // Method to get the keys of the object
    objectKeys(obj: any): string[] {
        return Object.keys(obj);
    }

    // Method to check if a value is an object
    isObject(value: any): boolean {
        return value && typeof value === 'object' && !Array.isArray(value);
    }

    sendMessage() {
        this.messages.push({
            role: this.role,
            contentShort: this.userMessage,
            content: this.userMessage,
            jsonObject: false
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
                this.findConfigurationsFunc()
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
            content: "Please provide the root folder of the project. This root folder should be in lowercase.",
            contentShort: "Please provide the root folder of the project. This root folder should be in lowercase.",
            jsonObject: false
        });

        //TODO remover
        this.userMessage = this.projectUuid
        //this.sendMessage()

    }

    findProjectFiles() {
        this.backend.findProjectFiles(this.projectUuid).subscribe((response: any) => {
            console.log(response);
            console.log(response[1]["content"]);

            //let content = JSON.parse(response[1]["content"])
            console.log(response[1]["content"]["ExecutableFiles"]);
            //console.log(content)
            //console.log(content["content"])


            this.messages.push(...response)

            //this.executableFiles = Object.values(response[1]["content"]['ExecutableFiles'])
            // Extract the necessary properties from the response for clarity
            const {ExecutableFiles, ConfigurationFiles} = response[1]["content"];

            // Assign the extracted values to class properties
            this.executableFiles = ExecutableFiles;
            this.configurationFiles = ConfigurationFiles;


            // Check if executable files exist and if there is more than one
            if (this.executableFiles?.length >= 1) {
                //this.changeStage(this.stages.FileToRun)
                //this.changeStage(this.stages.FindConfigurations)
                //this.stageAfterChat = this.stages.ParametersToUse
                this.changeStage(this.stages.ParametersToUse)

            } else if (this.executableFiles?.length == 1) {

                this.messageToAsk = "The file that you intent to run is " + this.executableFiles[0] + ". Can you confirm that this information is correct? Reply saying that you confirm or say the name of the file to run."
                //this.stageAfterChat = this.stages.ResearchArtifact
                this.changeStage(this.stages.WaitChatInteraction)
            } else {
                this.messages.push({
                    role: "assistant",
                    content: "There are no files to execute. ",
                    contentShort: "There are no files to execute",
                    jsonObject: false
                });
                this.changeStage(this.stages.ProjectLocation)
            }

            // Log the configuration and executable files for debugging
            console.log('Configuration Files:', this.configurationFiles);
            console.log('Executable Files:', this.executableFiles);


        });
    }


    parametersToUseFunc() {
        this.messages.push({
            role: "assistant",
            content: "Feel free to update any previous information. For example: I want to change the project location to exp26.\n"
                + "Now, tell me how to execute the experiment. For example: python ./myExampleFile.py",
            contentShort: "Feel free to update any previous information. For example: I want to change the project location to exp26.\n"
                + "Now, tell me how to execute the experiment. For example: python ./myExampleFile.py",
            jsonObject: false
        });

        //TODO remover
        this.userMessage = this.commandToRun
        //this.sendMessage()
    }

    parametersToUseConfirmation() {
        this.backend.parametersToUseConfirmation(this.projectUuid, this.messages).subscribe((response: any) => {
            switch (response[1].stage) {
                case "ParametersToUse":
                    if (response[1].contentShort) {
                        this.messages.push({
                            role: "assistant",
                            content: "The location of the project has been changed to" + response[1].content,
                            contentShort: "The location of the project has been changed to " + response[1].content,
                            jsonObject: false
                        });
                        this.projectUuid = response[1].content
                    } else {
                        this.messages.push({
                            role: "assistant",
                            content: response[1].content,
                            contentShort: response[1].content,
                            jsonObject: false
                        });
                    }
                    this.changeStage(this.stages.ParametersToUse)
                    break;

                case "ProjectLocation":
                    this.messages.push({
                        role: "assistant",
                        content: response[1].content,
                        contentShort: response[1].content,
                        jsonObject: false
                    });
                    this.changeStage(this.stages.ProjectLocation)
                    break;

                case "FindConfigurations":
                    this.commandToRun = response[1].content;
                    console.log("this.commandToRun " + this.commandToRun)
                    this.changeStage(this.stages.FindConfigurations)
                    break;

                default:
                    console.log('Unknown stage');
            }
        })
    }


    findConfigurations() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now infer all the necessary information to build the environment, which will take some time.",
            jsonObject: false
        });


        this.backend.findConfigurations(this.projectUuid, this.executableFiles).subscribe((response: any) => {
            console.log(response);
            this.messages.push(...response)

            let responseLength = response.length
            this.configurations = response[responseLength - 1].content

            this.changeStage(this.stages.BuildDockerFile)


            //this.changeStage(this.stages.BuildDockerFile)

        });
    }

    findConfigurationsInteraction() {
        this.messages.push({
            role: "assistant",
            content: "I used these settings. Are they correct, or would you like to change anything? \n" +
                JSON.stringify(this.configurations),
            contentShort: "I used these settings. Are they correct, or would you like to change anything? \n" +
                JSON.stringify(this.configurations),
            jsonObject: false
        });

    }

    findConfigurationsFunc() {
        this.backend.findConfigurationsFunc(this.projectUuid, this.messages).subscribe((response: any) => {
            console.log(response);
            this.messages.push(...response)
            let responseLength = response.length

            if (response[responseLength - 1].stage) {
                this.changeStage(response[responseLength - 1].stage)
            } else {
                this.configurations = response[responseLength - 1].content
                this.messageToAsk = "I used these settings. Are they correct, or would you like to change anything? \n" +
                    JSON.stringify(this.configurations)
                this.changeStage(this.stages.WaitChatInteraction)
                this.stageAfterChat = this.stages.BuildDockerFile
            }

        });
    }

    buildDockerFile() {
        this.backend.BuildDockerFile(this.projectUuid, this.messages).subscribe((response: any) => {
            console.log(response);
            this.messages.push(...response)
            this.changeStage(this.stages.BuildDockerImage)

            //TODO mudar
            //this.changeStage(this.stages.RunContainer)
            //this.changeStage(this.stages.Completed)
            //this.changeStage(this.stages.ResearchArtifact)

        });
    }

    buildDockerImage() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now build the environment to run the experiment, which will take some time.",
            jsonObject: false
        });
        this.backend.BuildDockerImage(this.projectUuid, this.messages).subscribe((response: any) => {
            console.log(response);
            this.messages.push(...response)
            if (!response[0].stage) {
                this.dockerImageID = response[0]["content"];
                console.log(this.dockerImageID)
                this.changeStage(this.stages.RunContainer)
            } else {
                this.changeStage(response[0].stage)
            }
        });
    }

    runContainer() {
        this.messages.push({
            role: "assistant",
            content: "",
            contentShort: "I will now run the experiment and provide you with the results as soon as possible.",
            jsonObject: false
        });
        console.log("asasas" + this.commandToRun)
        this.backend.RunContainer(this.projectUuid, this.dockerImageID, this.commandToRun, this.messages).subscribe((response: any) => {
            console.log(response);
            this.messages.push(...response)
            let responseLength = response.length
            if (!response[responseLength - 1].stage) {
                const {logs, added_files, removed_files, modified_files} = response[responseLength - 1]["content"];
                this.logs = logs;
                this.added_files = added_files;
                this.removed_files = removed_files
                this.modified_files = modified_files

                this.messageToAsk = "Can you confirm whether the result of the execution is correct? Please respond by either confirming or identifying what might have caused this unexpected result and proposing a solution.\n"
                this.stageAfterChat = this.stages.ResearchArtifact
                this.changeStage(this.stages.WaitChatInteraction)
            } else {
                this.changeStage(response[responseLength - 1].stage)
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
        this.backend.ResearchArtifact(this.projectUuid, this.dockerImageID, this.commandToRun, this.messages).subscribe((response: any) => {
            console.log("response");
            console.log(response);
            this.messages.push(...response)

            this.changeStage(this.stages.Completed)
        });
    }

    waitChatInteraction(messageToAsk: any) {
        console.log("aqui")

        this.messages.push({
            role: "assistant",
            content: messageToAsk,
            contentShort: messageToAsk,
            jsonObject: false
        });
    }

    chatInteraction() {
        this.backend.ChatInteraction(this.projectUuid, this.messages).subscribe((response: any) => {
            console.log(response);

            this.messages.push(...response)
            let responseLength = response.length
            if (response[responseLength - 1].stage == "NEXT") {
                this.changeStage(this.stageAfterChat)
            } else if (response[responseLength - 1].stage != this.stages.WaitChatInteraction) {
                this.changeStage(response[responseLength - 1].stage)
            } else {
                this.messageToAsk = "What might have caused this unexpected result, and what solution would you propose?\n"
                this.changeStage(this.stages.WaitChatInteraction)
            }

        });
    }


}