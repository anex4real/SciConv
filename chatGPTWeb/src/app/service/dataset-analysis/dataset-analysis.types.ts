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
    zenodoMetadataView?: ZenodoMetadataView;
}


export interface PersonView {
    name: string;
    affiliation?: string;
    orcid?: string;
    gnd?: string;
    type?: string; // contributors only
}

export interface RelatedIdentifierView {
    identifier: string;
    relation: string;
    resource_type?: string;
}

export interface SubjectView {
    term: string;
    identifier?: string;
    scheme?: string;
}

export interface LocationView {
    place: string;
    description?: string;
    lat?: number;
    lon?: number;
}

export interface DateRangeView {
    type: string;
    start?: string;
    end?: string;
    description?: string;
}

export interface ZenodoMetadataView {
    // --- Always visible ---
    title: string;
    doi?: string;
    publicationDate?: string;

    uploadType: string;
    publicationType?: string;
    imageType?: string;

    accessRight: string;
    license?: string;
    embargoDate?: string;
    accessConditions?: string;

    version?: string;
    language?: string;

    creators: PersonView[];
    contributors?: PersonView[];

    // --- Useful ---
    keywords?: string[];
    references?: string[];
    relatedIdentifiers?: RelatedIdentifierView[];
    communities?: string[];
    grants?: string[];

    description?: string;

    // --- Advanced (collapsible) ---
    notes?: string;
    method?: string;
    subjects?: SubjectView[];
    locations?: LocationView[];
    dates?: DateRangeView[];

    journal?: {
        title?: string;
        volume?: string;
        issue?: string;
        pages?: string;
    };

    conference?: {
        title?: string;
        acronym?: string;
        dates?: string;
        place?: string;
        url?: string;
        session?: string;
        session_part?: string;
    };

    imprint?: {
        publisher?: string;
        isbn?: string;
        place?: string;
    };

    partOf?: {
        title?: string;
        pages?: string;
    };

    thesis?: {
        supervisors?: string[];
        university?: string;
    };
}

