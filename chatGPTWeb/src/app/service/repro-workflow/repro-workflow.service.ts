// src/app/service/repro-workflow/repro-workflow.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { BackendService } from '../backend.service'; // <- ajusta se o teu ficheiro tiver outro nome/caminho
import { Message } from '../../interface/interfaces';
import { ReproState, ReproStages } from './repro-workflow.types';

@Injectable({ providedIn: 'root' })
export class ReproWorkflowService {
    private readonly initialState: ReproState = {
        stage: ReproStages.ProjectLocation,
        role: 'system',
        messages: [],
        projectUuid: '',
        commandToRun: '',
        executableFiles: undefined,
        configurationFiles: {},
        configurations: undefined,
        dockerImageID: undefined,
        logs: undefined,
        added_files: undefined,
        removed_files: undefined,
        modified_files: undefined,
        messageToAsk: undefined,
        examplesToAsk: undefined,
        stageAfterChat: undefined,
        isLoading: false,
        errorMessage: undefined,
        GO_BACK_NUMBER: 3,
        goBack: 3,
    };

    private readonly stateSubject = new BehaviorSubject<ReproState>(this.initialState);
    readonly state$ = this.stateSubject.asObservable();

    private get state(): ReproState {
        return this.stateSubject.value;
    }

    constructor(private backend: BackendService) {}

    private patch(p: Partial<ReproState>) {
        this.stateSubject.next({ ...this.state, ...p });
    }

    private pushMessages(...msgs: Message[]) {
        this.patch({ messages: [...this.state.messages, ...msgs] });
    }

    changeStage(newStage: ReproStages) {
        this.patch({ stage: newStage });
        this.performActionBasedOnStage(newStage);
    }

    // Chamado pelo HomeComponent quando o user envia texto
    sendUserMessage(userMessage: string) {
        this.pushMessages({
            role: this.state.role,
            contentShort: userMessage,
            content: userMessage,
            jsonObject: false,
        });

        switch (this.state.stage) {
            case ReproStages.ProjectLocation:
                this.patch({ projectUuid: userMessage });
                this.changeStage(ReproStages.FindProjectFiles);
                break;

            case ReproStages.ParametersToUse:
                this.parametersToUseConfirmation();
                break;

            case ReproStages.WaitChatInteraction:
                this.chatInteraction();
                break;

            case ReproStages.FindConfigurationsInteraction:
                this.findConfigurationsFunc(userMessage);
                break;

            case ReproStages.Completed:
                this.changeStage(ReproStages.ResearchArtifact);
                break;

            default:
                break;
        }
    }

    // Chamado pelo HomeComponent no submit do upload
    uploadProject(formData: FormData) {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.uploadProject(formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                const len = response.length;
                const last = response[len - 1];

                if (last.stage === ReproStages.FindProjectFiles) {
                    this.patch({ projectUuid: last.content });
                    this.changeStage(ReproStages.FindProjectFiles);
                } else if (last.stage) {
                    this.pushMessages(...response);
                    this.changeStage(last.stage);
                }
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Upload failed. Please check your connection or authentication.',
                });
            }
        });
    }

    private performActionBasedOnStage(stage: ReproStages) {
        switch (stage) {
            case ReproStages.ProjectLocation:
                this.projectLocation();
                break;
            case ReproStages.FindProjectFiles:
                this.findProjectFiles();
                break;
            case ReproStages.ParametersToUse:
                this.parametersToUseFunc();
                break;
            case ReproStages.FindConfigurations:
                this.findConfigurations();
                break;
            case ReproStages.FindConfigurationsInteraction:
                this.findConfigurationsInteraction();
                break;
            case ReproStages.WaitChatInteraction:
                this.waitChatInteraction(this.state.messageToAsk);
                break;
            case ReproStages.BuildDockerFile:
                this.buildDockerFile();
                break;
            case ReproStages.BuildDockerImage:
                this.buildDockerImage();
                break;
            case ReproStages.RunContainer:
                this.runContainer();
                break;
            case ReproStages.ResearchArtifact:
                this.researchArtifact();
                break;
            case ReproStages.Completed:
                break;
        }
    }




    private projectLocation() {
        this.pushMessages({
            role: "assistant",
            content: "Please provide the location of the project.",
            contentShort: "Please provide the location of the project.",
            jsonObject: false,
            examples:
                "Examples:\n" +
                "The root folder of the project is located at example_folder_name\n" +
                "example_folder_name"
        });
    }

    private findProjectFiles() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.findProjectFiles(this.state.projectUuid).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const len = response.length;
                const last = response[len - 1];

                if (last.stage === ReproStages.ParametersToUse) {
                    const { ExecutableFiles, ConfigurationFiles, ProjectUuid } = last.content;
                    this.patch({
                        executableFiles: ExecutableFiles,
                        configurationFiles: ConfigurationFiles,
                        projectUuid: ProjectUuid,
                    });
                }

                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to find project files. Please check your connection or authentication.",
                });
            }
        });
    }

    private parametersToUseFunc() {
        this.pushMessages({
            role: "assistant",
            content:
                "Enter the commands needed to run the experiment. I will execute them sequentially.\n" +
                "Example: python ./myfile.py && cd folder && python ./myfile2.py && cd .. && python ./myfile3.py",
            contentShort:
                "Please provide the commands required to run the experiment (executed sequentially).",
            jsonObject: false,
            examples:
                "Examples:\n" +
                "python ./main.py\n" +
                "python ./myfile.py && cd folder && python ./myfile2.py"
        });
    }

    private parametersToUseConfirmation() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.parametersToUseConfirmation(this.state.projectUuid, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const len = response.length;
                const last = response[len - 1];

                if (last.stage === ReproStages.FindConfigurations) {
                    this.patch({ commandToRun: last.content });
                }
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to confirm parameters. Please check your input or authentication.",
                });
            }
        });
    }

    private findConfigurations() {
        this.pushMessages({
            role: "assistant",
            content: "",
            contentShort: "I will now infer all the necessary information to build the environment, which can take some time.",
            jsonObject: false
        });

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.findConfigurations(this.state.projectUuid, this.state.executableFiles, this.state.commandToRun).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const len = response.length;
                const last = response[len - 1];

                this.patch({ configurations: last.content });
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to infer environment configuration. Please try again.",
                });
            }
        });
    }

    private findConfigurationsInteraction() {
        this.pushMessages({
            role: "assistant",
            content: "I used these settings. Are they correct, or would you like to change anything?\n" +
                JSON.stringify(this.state.configurations),
            contentShort: "I used these settings. Are they correct, or would you like to change anything?\n" +
                JSON.stringify(this.state.configurations),
            jsonObject: false,
            examples:
                "Change python version to 3.8.\n" +
                "Change pandas to 2.2.2.\n" +
                "Remove pandas.\n" +
                "Add c++.\n" +
                "I want: networkx==2.5 scikit-learn==0.23.2 tqdm==4.49.0 and python 3.8"
        });
    }

    private findConfigurationsFunc(userMessage: string) {
        this.patch({ isLoading: true, errorMessage: undefined });

        const myMessage =
            "Here are the configuration used: " + JSON.stringify(this.state.configurations) +
            "\nThe question is: Are they correct, or would you like to change anything?\n" +
            "The user action is: " + userMessage;

        this.backend.findConfigurationsFunc(this.state.projectUuid, this.state.messages, myMessage).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const len = response.length;
                const last = response[len - 1];

                if (last.stage === ReproStages.WaitChatInteraction) {
                    if (last.jsonObject === true) {
                        this.patch({ configurations: last.content });
                    }

                    this.patch({
                        examplesToAsk:
                            "I want to change the execution parameters.\n" +
                            "I want to change the project location.\n" +
                            "I want to change the computing environment used.\n",
                        messageToAsk:
                            "I used these settings. Are they correct, or would you like to change anything?\n" +
                            JSON.stringify(this.state.configurations),
                        stageAfterChat: ReproStages.BuildDockerFile
                    });
                }

                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to process configuration changes. Please try again.",
                });
            }
        });
    }

    private buildDockerFile() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.BuildDockerFile(this.state.projectUuid, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to build Dockerfile. Please try again.",
                });
            }
        });
    }

    private buildDockerImage() {
        this.pushMessages({
            role: "assistant",
            content: "",
            contentShort: "I will now build the environment to run the experiment, which can take some time.",
            jsonObject: false
        });

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.BuildDockerImage(this.state.projectUuid, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];

                if (last.goBack) {
                    const newGoBack = this.state.goBack - 1;

                    if (newGoBack <= 0) {
                        this.patch({ goBack: this.state.GO_BACK_NUMBER });
                        this.changeStage(ReproStages.FindConfigurationsInteraction);
                        return;
                    }
                    this.patch({ goBack: newGoBack });
                    this.auxFunction(response);
                    return;
                }

                this.auxFunction(response);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to build Docker image. Please verify the Dockerfile or environment.",
                });
            }
        });
    }

    private auxFunction(response: any) {
        const last = response[response.length - 1];

        if (last.stage === ReproStages.RunContainer) {
            this.patch({ dockerImageID: last.content });
        } else if (last.stage === ReproStages.WaitChatInteraction) {
            this.patch({ messageToAsk: undefined, stageAfterChat: ReproStages.FindConfigurations });
        }

        if (last.stage) this.changeStage(last.stage);
    }

    private runContainer() {
        this.pushMessages({
            role: "assistant",
            content: "",
            contentShort: "I will now run the experiment and provide you with the results as soon as possible.",
            jsonObject: false
        });

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.RunContainer(
            this.state.projectUuid,
            this.state.dockerImageID,
            this.state.commandToRun,
            this.state.messages
        ).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];

                if (!last.stage) {
                    const { logs, added_files, removed_files, modified_files } = last.content;

                    this.patch({
                        logs,
                        added_files,
                        removed_files,
                        modified_files,
                        messageToAsk:
                            "Can you confirm whether the result of the execution is correct?\n" +
                            "Please respond by either confirming or identifying what might have caused this unexpected result and proposing a solution.\n",
                        stageAfterChat: ReproStages.ResearchArtifact
                    });

                    this.changeStage(ReproStages.WaitChatInteraction);
                } else {
                    this.patch({ messageToAsk: undefined });
                    this.changeStage(last.stage);
                }
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to run container. Please review the command or image and try again.",
                });
            }
        });
    }

    private researchArtifact() {
        this.pushMessages({
            role: "assistant",
            content: "",
            contentShort: "I will now package all the experiment results into a zip folder and provide you with the result as soon as possible.",
            jsonObject: false
        });

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.ResearchArtifact(
            this.state.projectUuid,
            this.state.dockerImageID,
            this.state.commandToRun,
            this.state.messages
        ).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Failed to generate the research artifact. Please try again.",
                });
            }
        });
    }

    private waitChatInteraction(messageToAsk?: string) {
        if (!messageToAsk) return;

        const msg: Message = this.state.examplesToAsk
            ? {
                role: "assistant",
                content: messageToAsk,
                contentShort: messageToAsk,
                jsonObject: false,
                examples: this.state.examplesToAsk
            }
            : {
                role: "assistant",
                content: messageToAsk,
                contentShort: messageToAsk,
                jsonObject: false
            };

        this.pushMessages(msg);
        this.patch({ examplesToAsk: undefined });
    }

    private chatInteraction() {
        const nextStep = this.state.stageAfterChat ?? ReproStages.FindConfigurationsInteraction;

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.ChatInteraction(this.state.projectUuid, this.state.messages, nextStep).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];

                if (last.stage === ReproStages.WaitChatInteraction) {
                    this.patch({
                        messageToAsk: "What might have caused this unexpected result?\n",
                        examplesToAsk:
                            "I want to change the execution parameters.\n" +
                            "I want to change the project location.\n" +
                            "I want to change the computing environment used.\n"
                    });
                }

                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: "Chat interaction failed. Please try again.",
                });
            }
        });
    }

    reset() {
        this.stateSubject.next(this.initialState);
    }
}
