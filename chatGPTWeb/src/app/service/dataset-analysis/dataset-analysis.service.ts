// src/app/service/dataset-analysis/dataset-analysis.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { BackendService } from '../backend.service';
import { Message } from '../../interface/interfaces';
import { DataState, DataStages } from './dataset-analysis.types';

@Injectable({ providedIn: 'root' })
export class DatasetAnalysisService {

    private readonly initialState: DataState = {
        stage: DataStages.FindInformation,
        role: 'user',
        messages: [],
        articleUuid: '',

        referencedDatasets: [],
        nonReferencedDatasets: [],

        selectedAction: undefined,
        selectedDatasetName: undefined,

        messageToAsk: undefined,
        examplesToAsk: undefined,
        stageAfterChat: undefined,

        isLoading: false,
        errorMessage: undefined,

        GO_BACK_NUMBER: 3,
        goBack: 3,
    };

    private readonly stateSubject = new BehaviorSubject<DataState>(this.initialState);
    readonly state$ = this.stateSubject.asObservable();

    private get state(): DataState {
        return this.stateSubject.value;
    }

    constructor(private backend: BackendService) {}

    private patch(p: Partial<DataState>) {
        this.stateSubject.next({ ...this.state, ...p });
    }

    private pushMessages(...msgs: Message[]) {
        this.patch({ messages: [...this.state.messages, ...msgs] });
    }

    changeStage(newStage: DataStages) {
        this.patch({ stage: newStage });
        this.performActionBasedOnStage(newStage);
    }

    /** ========= 1) Upload PDF -> FindInformation ========= */
    findInformationArticle(formData: FormData) {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.findInformationArticle(formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response?.[response.length - 1];

                // Se o backend incluir articleUuid e listas de datasets no "content"
                // Ajusta se o teu backend usar outras keys.
                if (last?.content?.articleUuid) this.patch({ articleUuid: last.content.articleUuid });
                if (last?.content?.referencedDatasets) this.patch({ referencedDatasets: last.content.referencedDatasets });
                if (last?.content?.nonReferencedDatasets) this.patch({ nonReferencedDatasets: last.content.nonReferencedDatasets });

                if (last?.stage) this.changeStage(last.stage);
/*
                {
                    "author_datasets_with_references": [],
                    "author_datasets_without_references": [
                    "HospitalX-CXR Collection",
                    "the CT scan dataset"
                ]
                }*/
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Upload failed. Please check your connection or authentication.',
                });
            }
        });
    }

    /** ========= User typed + Send ========= */
    sendUserMessage(userMessage: string) {
        const text = (userMessage ?? '').trim();
        if (!text) return;

        // guardar mensagem do utilizador
        this.pushMessages({
            //role: this.state.role,
            role: "user",
            contentShort: text,
            content: text,
            jsonObject: false,
        });

        switch (this.state.stage) {
            case DataStages.DefineNextStepInteraction:
                // user escolhe infer/improve + dataset name (backend decide o próximo stage)
                this.chooseNextStepOnBackend();
                break;

            case DataStages.InferDatasetMetadata:
                // user forneceu nome do dataset não citado
                this.inferMetadataOnBackend(text);
                break;

            case DataStages.ImproveDatasetMetadata:
                // user forneceu nome do dataset citado
                this.improveMetadataOnBackend(text);
                break;

            case DataStages.WaitChatInteractionArticle:
                // fallback: manda o que o user disse ao backend e espera stage novo
                this.chatInteractionArticle();
                break;

            case DataStages.FindInformation:
            case DataStages.DatasetCompleted:
            default:
                // normalmente não esperamos input aqui
                break;
        }
    }

    /** ========= Stage-driven UI actions ========= */
    private performActionBasedOnStage(stage: DataStages) {
        switch (stage) {
            case DataStages.FindInformation:
                break;
            case DataStages.DefineNextStepInteraction:
                break;

            case DataStages.InferDatasetMetadata:
                this.askDatasetName('infer');
                break;

            case DataStages.ImproveDatasetMetadata:
                this.askDatasetName('improve');
                break;

            case DataStages.WaitChatInteractionArticle:
                this.waitChatInteractionArticle(this.state.messageToAsk);
                break;

            case DataStages.DatasetCompleted:
                // fim
                break;

            default:
                break;
        }
    }

    /** ========= Prompts ========= */

    private defineNextStepInteraction() {
        const ref = (this.state.referencedDatasets?.length ?? 0) > 0
            ? `Referenced datasets:\n- ${this.state.referencedDatasets!.join('\n- ')}\n\n`
            : 'Referenced datasets:\n- (none)\n\n';

        const nref = (this.state.nonReferencedDatasets?.length ?? 0) > 0
            ? `Non-referenced datasets:\n- ${this.state.nonReferencedDatasets!.join('\n- ')}\n\n`
            : 'Non-referenced datasets:\n- (none)\n\n';

        this.pushMessages({
            role: "assistant",
            content:
                "I analyzed the article and identified datasets used by the authors.\n\n" +
                ref + nref +
                "How would you like to proceed?\n\n" +
                "1) Infer metadata (dataset has no reference / identifier)\n" +
                "2) Improve metadata (dataset is referenced)\n" +
                "3) Edit dataset lists (add / update / delete referenced or non-referenced datasets)\n\n" +
                "Please provide your choice and the dataset name.\n" +
                "If you choose option 3, specify the operation (add/update/delete), the list (referenced/non-referenced), and the dataset name.",
            contentShort:
                "How would you like to proceed with the datasets?\n" +
                "Please provide your choice:\n" +
                "1) Infer metadata (no reference).\n" +
                "2) Improve metadata (referenced dataset).\n" +
                "3) Edit dataset lists (add/update/delete).\n",
            jsonObject: false,
            examples:
                "1) Infer metadata of Social Network Graph Dataset\n" +
                "2) Improve metadata of Climate Observations 1990–2020\n" +
                "3) Add to referenced: My Dataset | https://doi.org/10.xxxx/yyy\n" +
                "3) Delete from non-referenced: the CT scan dataset\n" +
                "3) Update referenced: Old Dataset Name -> New Dataset Name | https://doi.org/10.xxxx/zzz\n"
        });
    }

//todo TOBE delete show after improve infer action
    private askDatasetName(action: 'infer' | 'improve') {
        const label = action === 'infer' ? 'NON-referenced' : 'referenced';

        this.pushMessages({
            role: "assistant",
            content:
                `You selected "${action}". Please provide the name of the ${label} dataset you want to ${action}.`,
            contentShort:
                `Please provide the dataset name you want to ${action}.`,
            jsonObject: false,
            examples:
                action === 'infer'
                    ? "Example: Social Network Graph Dataset"
                    : "Example: Climate Observations 1990–2020"
        });
    }

    private waitChatInteractionArticle(messageToAsk?: string) {
        if (!messageToAsk) return;

        const msg: Message = this.state.examplesToAsk
            ? { role: "assistant", content: messageToAsk, contentShort: messageToAsk, jsonObject: false, examples: this.state.examplesToAsk }
            : { role: "assistant", content: messageToAsk, contentShort: messageToAsk, jsonObject: false };

        this.pushMessages(msg);
        this.patch({ examplesToAsk: undefined });
    }

    /** ========= Backend calls ========= */

    // backend interpreta a última resposta do user e devolve stage: InferDatasetMetadata ou ImproveDatasetMetadata
    private chooseNextStepOnBackend() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.datasetChooseNextStep(this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response?.[response.length - 1];
                const c = last?.content;

                //  Update lists if backend returned them (edit flow)
                if (c?.referencedDatasets) this.patch({ referencedDatasets: c.referencedDatasets });
                if (c?.nonReferencedDatasets) this.patch({ nonReferencedDatasets: c.nonReferencedDatasets });

                //  Infer/Improve decision flow
                if (c?.action) this.patch({ selectedAction: c.action });
                if (c?.dataset_name) this.patch({ selectedDatasetName: c.dataset_name });

                if (last?.stage) {
                    this.patch({ stage: last.stage });

                    // If backend says we’re back at DefineNextStepInteraction, show your important message
                    if (last.stage === DataStages.DefineNextStepInteraction) {
                        //this.defineNextStepInteraction();
                        return;
                    }

                    // otherwise continue normal stage-driven actions
                    this.performActionBasedOnStage(last.stage);
                }
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to process your choice. Please try again.',
                });
            }
        });
    }


    private inferMetadataOnBackend(datasetName: string) {
        this.patch({ isLoading: true, errorMessage: undefined, selectedAction: 'infer', selectedDatasetName: datasetName });

        this.backend.datasetInferMetadata(this.state.articleUuid, datasetName, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response?.[response.length - 1];
                if (last?.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to infer dataset metadata. Please try again.',
                });
            }
        });
    }

    private improveMetadataOnBackend(datasetName: string) {
        this.patch({ isLoading: true, errorMessage: undefined, selectedAction: 'improve', selectedDatasetName: datasetName });

        this.backend.datasetImproveMetadata(this.state.articleUuid, datasetName, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response?.[response.length - 1];
                if (last?.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to improve dataset metadata. Please try again.',
                });
            }
        });
    }

    // opcional: se quiseres um endpoint genérico para interações
    private chatInteractionArticle() {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.articleChatInteraction(this.state.articleUuid, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                this.pushMessages(...response);

                const last = response?.[response.length - 1];
                if (last?.stage) this.changeStage(last.stage);
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Chat interaction failed. Please try again.',
                });
            }
        });
    }

    reset() {
        this.stateSubject.next(this.initialState);
    }
}