import {Message} from "../../interface/interfaces";

export enum DataStages {
    FindInformation = 'FindInformation',
    DefineNextStepInteraction = 'DefineNextStepInteraction',
    InferDatasetMetadata = 'InferDatasetMetadata',
    ImproveDatasetMetadata = 'ImproveDatasetMetadata',
    WaitChatInteractionArticle = 'WaitChatInteractionArticle',
    DatasetCompleted = 'DatasetCompleted'
}

export interface DataState {
    stage: DataStages;
    role: string;
    messages: Message[];
    messageToAsk?: string;
    examplesToAsk?: string;
    stageAfterChat?: DataStages;


    referencedDatasets?: string[];
    nonReferencedDatasets?: string[];

    selectedAction?: 'infer' | 'improve';
    selectedDatasetName?: string;

    isLoading: boolean;
    errorMessage?: string;
    readonly GO_BACK_NUMBER: number;
    goBack: number;
    articleUuid: string;

}
