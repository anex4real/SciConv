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
        outputSpec: '',
        runProgressDetail: '',
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
        artifactZenodoDoi: undefined,
        artifactIsUploading: false,
        datasetMetadataDraft: undefined,
        datasetMetadataTemplate: undefined,
        datasetMetadataReady: false,
        artifactMetadataDraft: undefined,
        artifactMetadataReady: false,
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

            case ReproStages.SpecifyOutputs:
                this.specifyOutputsConfirmation();
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
                    // Try to infer dataset metadata first; backend returns skip:true
                    // for strategies that don't upload to Zenodo.
                    this.changeStage(ReproStages.InferDatasetMetadata);
                } else if (last.stage) {
                    this.pushMessages(...response);
                    this.changeStage(last.stage);
                }
            },
            error: (err: any) => {
                console.error('[UploadProject] HTTP', err?.status, err?.error);
                this.patch({
                    isLoading: false,
                    errorMessage: `Upload failed (HTTP ${err?.status ?? 'network error'}). Please check your connection or authentication.`,
                });
            }
        });
    }

    private performActionBasedOnStage(stage: ReproStages) {
        switch (stage) {
            case ReproStages.ProjectLocation:
                this.projectLocation();
                break;
            case ReproStages.InferDatasetMetadata:
                this.inferDatasetMetadata();
                break;
            case ReproStages.ExternalizeData:
                this.externalizeData();
                break;
            case ReproStages.FindProjectFiles:
                this.findProjectFiles();
                break;
            case ReproStages.ParametersToUse:
                this.parametersToUseFunc();
                break;
            case ReproStages.SpecifyOutputs:
                this.specifyOutputsFunc();
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

    private inferDatasetMetadata() {
        this.patch({ isLoading: true, errorMessage: undefined, datasetMetadataReady: false });

        this.pushMessages({
            role: 'assistant',
            content: 'Analysing dataset to infer Zenodo metadata...',
            contentShort: 'Analysing dataset to infer Zenodo metadata...',
            jsonObject: false,
        });

        this.backend.inferDatasetMetadata(this.state.projectUuid).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                if (response.skip) {
                    // Strategy doesn't need Zenodo upload — proceed automatically
                    this.changeStage(ReproStages.ExternalizeData);
                    return;
                }
                const metadataList = response.zenodo_metadata || [];
                const draft = metadataList.length > 0 ? metadataList[0].metadata : {};
                this.patch({
                    datasetMetadataDraft: draft,
                    datasetMetadataTemplate: response.template,
                    datasetMetadataReady: true,
                });
            },
            error: () => {
                // On inference failure, skip metadata and proceed
                this.patch({ isLoading: false });
                this.changeStage(ReproStages.ExternalizeData);
            }
        });
    }

    confirmDatasetMetadata(metadata: any) {
        this.patch({ datasetMetadataReady: false, isLoading: true, errorMessage: undefined });

        this.pushMessages({
            role: 'assistant',
            content: 'Processing dataset (this may take a few minutes for large files)...',
            contentShort: 'Processing dataset...',
            jsonObject: false,
        });

        this.backend.externalizeData(this.state.projectUuid, metadata).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);
                this.changeStage(ReproStages.FindProjectFiles);
            },
            error: (err: any) => {
                const status = err?.status ?? 'network error';
                const body = err?.error;
                const detail = Array.isArray(body)
                    ? body.map((m: any) => m.contentShort || m.content).join(' | ')
                    : (typeof body === 'string' ? body : JSON.stringify(body ?? {}));
                this.patch({
                    isLoading: false,
                    errorMessage: `Dataset upload failed (HTTP ${status}): ${detail}`,
                });
            }
        });
    }

    skipDatasetMetadata() {
        this.patch({ datasetMetadataReady: false });
        this.changeStage(ReproStages.ExternalizeData);
    }

    private externalizeData() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.pushMessages({
            role: 'assistant',
            content: 'Processing dataset (this may take a few minutes for large files)...',
            contentShort: 'Processing dataset...',
            jsonObject: false,
        });

        this.backend.externalizeData(this.state.projectUuid).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);
                this.changeStage(ReproStages.FindProjectFiles);
            },
            error: (err: any) => {
                const status = err?.status ?? 'network error';
                const body = err?.error;
                const detail = Array.isArray(body)
                    ? body.map((m: any) => m.contentShort || m.content).join(' | ')
                    : (typeof body === 'string' ? body : JSON.stringify(body ?? {}));
                console.error('[ExternalizeData] HTTP', status, detail);
                this.patch({
                    isLoading: false,
                    errorMessage: `Dataset upload failed (HTTP ${status}): ${detail}`,
                });
            }
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

                if (last.stage === ReproStages.SpecifyOutputs) {
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

    private specifyOutputsFunc() {
        this.pushMessages({
            role: 'assistant',
            content:
                'Please specify the output files or directories your experiment creates.\n' +
                'Use space-separated paths or glob patterns relative to the working directory.\n' +
                'Example: results/ models/*.pkl report.pdf',
            contentShort: 'Please specify the output files or directories your experiment creates.',
            jsonObject: false,
            examples:
                'Examples:\n' +
                'results/\n' +
                'output/*.csv\n' +
                'results/ models/*.pkl report.pdf'
        });
    }

    private specifyOutputsConfirmation() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.specifyOutputs(this.state.projectUuid, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const len = response.length;
                const last = response[len - 1];

                if (last.stage === ReproStages.FindConfigurations) {
                    this.patch({ outputSpec: last.content });
                }
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to save output specification.',
                });
            }
        });
    }

    skipOutputSpec() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.skipOutputs(this.state.projectUuid).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response[response.length - 1];
                if (last.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to skip output specification.',
                });
            }
        });
    }

    uploadArtifact() {
        // Step 1: infer metadata via GPT, show editor before uploading
        this.patch({ artifactIsUploading: true, errorMessage: undefined, artifactMetadataReady: false });

        this.backend.inferArtifactMetadata(this.state.projectUuid).subscribe({
            next: (res: any) => {
                this.patch({
                    artifactIsUploading: false,
                    artifactMetadataDraft: {
                        title: res.title || '',
                        description: res.description || '',
                        creator_name: '',
                    },
                    artifactMetadataReady: true,
                    stage: ReproStages.InferArtifactMetadata,
                });
            },
            error: () => {
                // Fall back to uploading with generic metadata
                this.patch({ artifactIsUploading: false });
                this._doUploadArtifact({});
            }
        });
    }

    confirmArtifactMetadata(draft: { title: string; description: string; creator_name: string }) {
        this._doUploadArtifact(draft);
    }

    skipArtifactMetadata() {
        this._doUploadArtifact({});
    }

    private _doUploadArtifact(body: any) {
        this.patch({ artifactIsUploading: true, errorMessage: undefined, stage: ReproStages.Completed });

        this.backend.uploadArtifactToZenodo(this.state.projectUuid, body).subscribe({
            next: (response: any) => {
                this.patch({ artifactIsUploading: false });
                this.pushMessages(...response);
                const last = response[response.length - 1];
                const doi = last?.content?.doi || last?.contentShort?.match(/DOI: (.+)/)?.[1];
                if (doi) this.patch({ artifactZenodoDoi: doi });
            },
            error: () => {
                this.patch({
                    artifactIsUploading: false,
                    errorMessage: 'Failed to upload artifact to Zenodo.',
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

        this.patch({ isLoading: true, errorMessage: undefined, runProgressDetail: '' });

        // Poll run_progress.json every 2 s while the request is in-flight
        const pollId = window.setInterval(() => {
            this.backend.getRunProgress(this.state.projectUuid).subscribe({
                next: (p: any) => {
                    if (p?.detail) {
                        this.patch({ runProgressDetail: p.detail });
                    }
                }
            });
        }, 2000);

        this.backend.RunContainer(
            this.state.projectUuid,
            this.state.dockerImageID,
            this.state.commandToRun,
            this.state.messages
        ).subscribe({
            next: (response: any) => {
                window.clearInterval(pollId);
                this.patch({ isLoading: false, runProgressDetail: '' });
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
                window.clearInterval(pollId);
                this.patch({
                    isLoading: false,
                    runProgressDetail: '',
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
