// src/app/service/repro-workflow/repro-workflow.types.ts
import { Message } from "../../interface/interfaces";
import {ZenodoMetadataView} from "../dataset-analysis/dataset-analysis.types";

export enum ReproStages {
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

export interface ReproState {
    stage: ReproStages;
    role: string;
    messages: Message[];
    projectUuid: string;
    commandToRun: string;
    executableFiles: any;
    configurationFiles: any;
    configurations: any;
    dockerImageID: any;
    logs: any;
    added_files: any;
    removed_files: any;
    modified_files: any;
    messageToAsk?: string;
    examplesToAsk?: string;
    stageAfterChat?: ReproStages;
    isLoading: boolean;
    errorMessage?: string;
    goBack: number;
    readonly GO_BACK_NUMBER: number;
}