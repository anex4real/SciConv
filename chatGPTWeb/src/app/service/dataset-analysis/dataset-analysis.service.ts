// src/app/service/dataset-analysis/dataset-analysis.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { BackendService } from '../backend.service';
import { Message } from '../../interface/interfaces';
import {DataState, DataStages, ZenodoMetadataView} from './dataset-analysis.types';

@Injectable({ providedIn: 'root' })
export class DatasetAnalysisService {

    private readonly initialState: DataState = {
        stage: DataStages.FindInformation,
        role: 'user',
        messages: [],
        articleUuid: '',
        zenodoMetadataView: undefined,

        referencedDatasets: [],
        nonReferencedDatasets: [],

        availableActions: [],

        uiInstructions: undefined,
        uiAction: undefined,
        uiListKind: undefined,
        uiDatasetName: undefined,
        uiZenodoRef: undefined,
        uiNewDatasetName: undefined,

        selectedAction: undefined,
        selectedDatasetName: undefined,

        messageToAsk: undefined,
        examplesToAsk: undefined,
        stageAfterChat: undefined,

        isLoading: false,
        errorMessage: undefined,
        zenodoTemplate: undefined,
        zenodoMetadataDraft: undefined,

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

        this.backend.uploadArticleFindInformation(formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                const articleUuid = response?.article_uuid;
                if (articleUuid) this.patch({ articleUuid });

                const actions = response?.actions ?? [];
                this.patch({ availableActions: actions, menuActions: actions }); // ✅ save initial menu

                const msgs = response?.messages ?? [];
                this.pushMessages(...msgs);

                this.patch({ menuMessages: msgs });

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;

                if (c?.instructions) this.patch({ uiInstructions: c.instructions });

                // if (c?.zenodo_metadata) {
                //     this.patch({ zenodoMetadataView: this.buildZenodoMetadataView(c.zenodo_metadata) });
                // }

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

    selectAction(action: string) {
        const a = (action || '').toLowerCase().trim() as any;

        // ✅ handle go to menu immediately
        if (a === 'go to menu') {
            this.goToMenu();
            return;
        }

        this.patch({
            uiAction: a,
            uiListKind: undefined,
            uiDatasetName: undefined,
            uiZenodoRef: undefined,
            uiNewDatasetName: undefined,
            errorMessage: undefined,
        });

        // IMPORTANT: do NOT change stages here.
        // The UI form will appear and user will click Send.
    }
    saveEditedMetadata() {
        const draft = this.state.zenodoMetadataDraft;
        const template = this.state.zenodoTemplate;

        if (!draft) {
            this.patch({ errorMessage: 'Missing metadata draft.' });
            return;
        }


        this.patch({
            zenodoMetadataDraft: this.deepClone(draft),
            errorMessage: undefined
        });
    }



    submitActionForm(): boolean {
        const a = this.state.uiAction;
        if (!a) return false; // nothing to submit

        if (a === 'update metadata') {
            if (!this.state.zenodoTemplate || !this.state.zenodoMetadataDraft) {
                this.patch({ errorMessage: 'No metadata/template available. Please run infer or improve first.' });
                return true;
            }

            this.patch({
                stage: DataStages.EditZenodoMetadata,
                errorMessage: undefined,
            });

            this.clearUiActionForm();
            return true;
        }



        // ---------- CREATE (backend) ----------
        if (a === 'create') {
            const datasetName = (this.state.activeDatasetName || '').trim();
            if (!datasetName) {
                this.patch({ errorMessage: 'Please select a dataset to create on Zenodo.' });
                return true;
            }

            this.createRepositoryOnBackend(
                datasetName,
                this.state.nonReferencedDatasets ?? [],
                this.state.referencedDatasets ?? []
            );

            this.clearUiActionForm();
            return true;
        }


        // ---------- INFER (backend) ----------
        if (a === 'infer') {
            const name = (this.state.uiDatasetName || '').trim();
            this.patch({ activeDatasetName: name });
            if (!name) {
                this.patch({ errorMessage: 'Please select a dataset from the non-referenced list.' });
                return true;
            }
            this.inferMetadataOnBackend(name);
            this.clearUiActionForm();
            return true;
        }

        // ---------- IMPROVE (backend) ----------
        if (a === 'improve') {
            const name = (this.state.uiDatasetName || '').trim();
            if (!name) {
                this.patch({ errorMessage: 'Please select a dataset from the referenced list.' });
                return true;
            }
            this.improveMetadataOnBackend(name);
            this.clearUiActionForm();
            return true;
        }

        // ---------- ADD / DELETE / UPDATE (LOCAL) ----------
        const listKind = this.state.uiListKind;
        if (!listKind) {
            this.patch({ errorMessage: 'Please select referenced or non-referenced list.' });
            return true;
        }

        const referenced = [...(this.state.referencedDatasets ?? [])];
        const nonReferenced = [...(this.state.nonReferencedDatasets ?? [])];

        // ---------- ADD ----------
        if (a === 'add') {
            const name = (this.state.uiDatasetName || '').trim();
            if (!name) {
                this.patch({ errorMessage: 'Please type the dataset name to add.' });
                return true;
            }

            if (listKind === 'non-referenced') {
                const exists = nonReferenced.some(d => d.toLowerCase() === name.toLowerCase());
                if (exists) {
                    this.patch({ errorMessage: 'This dataset already exists in non-referenced list.' });
                    return true;
                }

                nonReferenced.push(name);
                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({ action: 'add', list: 'referenced', added: name }, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced add: need name + ref
            const ref = (this.state.uiZenodoRef || '').trim();
            if (!ref) {
                this.patch({ errorMessage: 'Please provide Zenodo DOI/URL.' });
                return true;
            }

            const exists = referenced.some(e => this.refEntryName(e).toLowerCase() === name.toLowerCase());
            if (exists) {
                this.patch({ errorMessage: 'This dataset already exists in referenced list.' });
                return true;
            }

            const entry = this.buildRefEntry(name, ref);
            referenced.push(entry);
            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({ action: 'add', list: 'non-referenced', added: name }, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        // ---------- DELETE ----------
        if (a === 'delete') {
            const name = (this.state.uiDatasetName || '').trim();
            if (!name) {
                this.patch({ errorMessage: 'Please choose a dataset to delete.' });
                return true;
            }

            if (listKind === 'non-referenced') {
                const idx = nonReferenced.findIndex(d => d.toLowerCase() === name.toLowerCase());
                if (idx < 0) {
                    this.patch({ errorMessage: 'Dataset not found in non-referenced list.' });
                    return true;
                }

                const deleted = nonReferenced[idx];
                nonReferenced.splice(idx, 1);
                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({ action: 'delete', list: 'non-referenced', deleted }, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced delete by dataset name (left side)
            const idx = referenced.findIndex(e => this.refEntryName(e).toLowerCase() === name.toLowerCase());
            if (idx < 0) {
                this.patch({ errorMessage: 'Dataset not found in referenced list.' });
                return true;
            }

            const deleted = referenced[idx];
            referenced.splice(idx, 1);
            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({ action: 'delete', list: 'referenced', deleted }, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        // ---------- UPDATE ----------
        if (a === 'update') {
            const oldName = (this.state.uiDatasetName || '').trim();
            if (!oldName) {
                this.patch({ errorMessage: 'Please choose a dataset to update.' });
                return true;
            }

            const newName = (this.state.uiNewDatasetName || '').trim();
            const newRef = (this.state.uiZenodoRef || '').trim();

            if (!newName && !newRef) {
                this.patch({ errorMessage: 'Please edit at least one field (new name and/or Zenodo ref).' });
                return true;
            }

            if (listKind === 'non-referenced') {
                const idx = nonReferenced.findIndex(d => d.toLowerCase() === oldName.toLowerCase());
                if (idx < 0) {
                    this.patch({ errorMessage: 'Dataset not found in non-referenced list.' });
                    return true;
                }

                const finalName = newName || nonReferenced[idx];

                // prevent duplicates (other than itself)
                const dup = nonReferenced.some((d, i) =>
                    i !== idx && d.toLowerCase() === finalName.toLowerCase()
                );
                if (dup) {
                    this.patch({ errorMessage: 'Another dataset already has that name.' });
                    return true;
                }

                const before = nonReferenced[idx];
                nonReferenced[idx] = finalName;

                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({ action: 'update', list: 'non-referenced', from: before, to: finalName }, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced update
            const idx = referenced.findIndex(e => this.refEntryName(e).toLowerCase() === oldName.toLowerCase());
            if (idx < 0) {
                this.patch({ errorMessage: 'Dataset not found in referenced list.' });
                return true;
            }

            const before = referenced[idx];
            const oldLink = this.refEntryLink(before);

            const finalName = newName || this.refEntryName(before);
            const finalLink = newRef || oldLink;

            if (!finalLink) {
                this.patch({ errorMessage: 'Referenced dataset must have a Zenodo DOI/URL.' });
                return true;
            }

            // prevent duplicates by name (except itself)
            const dup = referenced.some((e, i) =>
                i !== idx && this.refEntryName(e).toLowerCase() === finalName.toLowerCase()
            );
            if (dup) {
                this.patch({ errorMessage: 'Another referenced dataset already has that name.' });
                return true;
            }

            const after = this.buildRefEntry(finalName, finalLink);
            referenced[idx] = after;

            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({ action: 'update', list: 'referenced', from: before, to: after }, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        return true;
    }
    private rebuildMenuMessagesWithCurrentLists(): Message[] {
        const menuMessages = [...(this.state.menuMessages ?? [])];
        if (!menuMessages.length) return menuMessages;

        const active = (this.state.activeDatasetName || '').trim();
        const instructions = this.state.uiInstructions ?? '';

        // Start from CURRENT state lists
        let referenced = [...(this.state.referencedDatasets ?? [])];
        let nonReferenced = [...(this.state.nonReferencedDatasets ?? [])];

        // ✅ If we have an active dataset, move it from non-referenced -> referenced
        if (active) {
            // 1) remove from non-referenced
            const newNonReferenced = nonReferenced.filter(
                d => d.toLowerCase() !== active.toLowerCase()
            );

            // 2) build referenced entry using DOI if available
            const doi = (this.state.zenodoMetadataView?.doi || '').trim();
            const link = doi ? `https://doi.org/${doi}` : '';

            const entryWithLink = link ? `${active} | ${link}` : active;

            // 3) upsert into referenced list (by dataset name)
            const idx = referenced.findIndex(
                e => this.refEntryName(e).toLowerCase() === active.toLowerCase()
            );

            let newReferenced = [...referenced];
            if (idx >= 0) {
                // Prefer the DOI version if we now have it
                const current = newReferenced[idx];
                const currentHasLink = !!this.refEntryLink(current);
                if (!currentHasLink && link) {
                    newReferenced[idx] = entryWithLink;
                }
            } else {
                newReferenced.push(entryWithLink);
            }

            // ✅ 4) commit into STATE (this is what you asked for)
            referenced = newReferenced;
            nonReferenced = newNonReferenced;

            this.patch({
                referencedDatasets: referenced,
                nonReferencedDatasets: nonReferenced,
            });
        }

        // ✅ recompute summary
        const newSummary =
            `I found datasets in the article.\n` +
            `Referenced: ${referenced.length}\n` +
            `Not referenced: ${nonReferenced.length}`;

        // ✅ update the menu message snapshot (lists + summary)
        for (let i = menuMessages.length - 1; i >= 0; i--) {
            const m: any = menuMessages[i];
            if (!m?.jsonObject) continue;

            const cShort = m?.contentShort;
            const cFull = m?.content;

            const hasLists =
                cShort && typeof cShort === 'object' &&
                ('referencedDatasets' in cShort || 'nonReferencedDatasets' in cShort);

            if (!hasLists) continue;

            menuMessages[i] = {
                ...m,
                contentShort: {
                    ...(cShort ?? {}),
                    summary: newSummary,
                    referencedDatasets: referenced,
                    nonReferencedDatasets: nonReferenced,
                    instructions,
                },
                content: {
                    ...(cFull ?? {}),
                    summary: newSummary,
                    referencedDatasets: referenced,
                    nonReferencedDatasets: nonReferenced,
                    instructions,
                }
            };

            break;
        }

        this.patch({ menuMessages });

        return menuMessages;
    }

    private goToMenu() {
        const menuActions = this.state.menuActions ?? [];
        const rebuiltMenuMessages = this.rebuildMenuMessagesWithCurrentLists();

        this.patch({
            stage: DataStages.DefineNextStepInteraction,
            availableActions: menuActions.length ? menuActions : this.state.availableActions,
            messages: rebuiltMenuMessages.length ? rebuiltMenuMessages : this.state.messages,

            referencedDatasets: this.state.referencedDatasets,
            nonReferencedDatasets: this.state.nonReferencedDatasets,

            uiInstructions: this.state.uiInstructions,

            uiAction: undefined,
            uiListKind: undefined,
            uiDatasetName: undefined,
            uiZenodoRef: undefined,
            uiNewDatasetName: undefined,
            errorMessage: undefined,
        });
    }
    editZenodoOnBackend(cleanedMetadata: any, zenodoToken?: string) {
        const articleUuid = this.state.articleUuid;
        let depositionId = this.state.depositionId;

        if (!articleUuid) {
            this.patch({ errorMessage: 'Missing article UUID.' });
            return;
        }
        //todo
        depositionId=1234
        /*if (!depositionId) {
            this.patch({ errorMessage: 'Missing deposition id. Create the Zenodo deposition first.' });
            return;
        }*/

        const formData = new FormData();

        // ✅ backend requires top-level "metadata"
        formData.append('metadata', JSON.stringify({ metadata: cleanedMetadata }));

        // optional token
        if (zenodoToken) formData.append('zenodo_token', zenodoToken);

        // optional flag
        formData.append('replace_files', 'false');

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.datasetEditZenodo(articleUuid, depositionId, formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                // if backend returns updated deposition/metadata you can refresh view here
                const dep = response?.deposition;
                const meta = dep?.metadata ? { metadata: dep.metadata } : null;

                if (meta) {
                    this.patch({
                        zenodoMetadataView: this.buildZenodoMetadataView(meta),
                        zenodoMetadataDraft: this.deepClone(dep.metadata),
                    });
                }

                // go back to menu
                this.selectAction('go to menu');
            },
            error: () => {
                this.patch({ isLoading: false, errorMessage: 'Failed to edit Zenodo deposition.' });
            }
        });
    }


    private createRepositoryOnBackend( datasetName: string,
                                       nonReferenced: string[] = [],
                                       referenced: string[] = []) {
        this.patch({ isLoading: true, errorMessage: undefined });

        const zm = this.state.zenodoMetadataView;
        if (!zm) {
            this.patch({ isLoading: false, errorMessage: 'No Zenodo metadata available.' });
            return;
        }

        // ✅ backend requires: top-level key "metadata"
        const metadataPayload = {
            metadata: this.serializeZenodoMetadata(zm),
        };

        const formData = new FormData();
        formData.append('metadata', JSON.stringify(metadataPayload));

        // ✅ If you have files to upload, append them:
        // Example: if you stored selected files in state as File[]
        // for (const f of (this.state.selectedFiles ?? [])) {
        //   formData.append('files', f, f.name);
        // }

        this.backend.datasetCreateZenodo(this.state.articleUuid, formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });
                const actions = response?.actions ?? [];
                this.patch({ availableActions: actions });

                const zmRaw = response?.zenodo_metadata;
                if (!zmRaw) return;

                // ✅ build view once
                const view = this.buildZenodoMetadataView(zmRaw);
                this.patch({ zenodoMetadataView: view });

                // ✅ DOI is available immediately here
                const doi = (view.doi || '').trim();
                const link = doi ? `https://doi.org/${doi}` : '';

                // ✅ now update lists
                const datasetName = (/* the dataset selected for creation */ '').trim();

                if (datasetName && link) {
                    const newNonRef = (this.state.nonReferencedDatasets ?? [])
                        .filter(d => d.toLowerCase() !== datasetName.toLowerCase());

                    const newRef = [...(this.state.referencedDatasets ?? [])];
                    const entry = `${datasetName} | ${link}`;

                    const idx = newRef.findIndex(e =>
                        this.refEntryName(e).toLowerCase() === datasetName.toLowerCase()
                    );
                    if (idx >= 0) newRef[idx] = entry;
                    else newRef.push(entry);

                    this.patch({ nonReferencedDatasets: newNonRef, referencedDatasets: newRef });

                    // update menu snapshot if you use it
                    this.updateMenuSnapshotLists(newRef, newNonRef);
                }
            }            ,
            error: (err) => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to create Zenodo repository.'
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
            case DataStages.ImproveDatasetMetadata:
                // no chat prompt; UI form handles it
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

    private refEntryName(entry: string): string {
        return (entry || '').split('|')[0].trim();
    }

    private refEntryLink(entry: string): string {
        return ((entry || '').split('|')[1] || '').trim();
    }

    private buildRefEntry(name: string, ref: string): string {
        return `${name.trim()} | ${ref.trim()}`;
    }


    private clearUiActionForm() {
        this.patch({
            uiAction: undefined,
            uiListKind: undefined,
            uiDatasetName: undefined,
            uiZenodoRef: undefined,
            uiNewDatasetName: undefined,
        });
    }

    private patchLists(referenced: string[], nonReferenced: string[]) {
        this.patch({ referencedDatasets: referenced, nonReferencedDatasets: nonReferenced });
    }

    private pushLocalEditMessage(summary: any, referenced?: string[], nonReferenced?: string[]) {
        const ref = referenced ?? this.state.referencedDatasets ?? [];
        const nref = nonReferenced ?? this.state.nonReferencedDatasets ?? [];

        this.pushMessages({
            role: 'assistant',
            jsonObject: true,
            contentShort: {
                ...summary,
                referencedDatasets: ref,
                nonReferencedDatasets: nref,
                // ✅ reuse backend instructions here
                instructions: this.state.uiInstructions ?? ''
            },
            // keep content same shape as contentShort if you want consistency
            content: {
                ...summary,
                referencedDatasets: ref,
                nonReferencedDatasets: nref,
                instructions: this.state.uiInstructions ?? ''
            } as any,
        });
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

        /*  this.backend.datasetChooseNextStep(this.state.articleUuid,this.state.messages).subscribe({
              next: (response: any) => {
                  this.patch({ isLoading: false });
                  this.pushMessages(...response);

                  const last = response?.[response.length - 1];
                  const c = last?.content ?? last?.contentShort;
                  if (c?.zenodo_metadata) {
                      this.patch({ zenodoMetadataView: this.buildZenodoMetadataView(c.zenodo_metadata) });
                  }

                  if (c?.instructions) this.patch({ uiInstructions: c.instructions });

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
          });*/
    }

    private inferMetadataOnBackend(datasetName: string) {
        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend
            .datasetInferMetadata(this.state.articleUuid, datasetName, this.state.messages)
            .subscribe({
                next: (response: any) => {
                    this.patch({ isLoading: false });

                    // ✅ response is { actions, messages }
                    const actions = response?.actions ?? [];
                    const msgs = response?.messages ?? [];

                    this.patch({ availableActions: actions });
                    this.pushMessages(...msgs);

                    const last = msgs?.[msgs.length - 1];

                    // ✅ IMPORTANT: prefer content, fallback to contentShort
                    const c = last?.content ?? last?.contentShort;

                    if (c?.instructions) this.patch({ uiInstructions: c.instructions });

                    // ---- 1) template/schema ----
                    const tplRaw = c?.template;
                    const templateObj = (tplRaw?.metadata ?? tplRaw) ?? undefined;

                    if (templateObj) {
                        this.patch({ zenodoTemplate: templateObj });
                    }

                    // ---- 2) metadata/values ----
                    const zmRaw = c?.zenodo_metadata;

                    if (zmRaw) {
                        const first = Array.isArray(zmRaw) ? (zmRaw[0] ?? {}) : zmRaw;
                        const metadataObj = (first?.metadata ?? first) ?? {};

                        // ✅ summary view (your existing UI)
                        const view = this.buildZenodoMetadataView(zmRaw);

                        // ✅ draft MUST be ONLY values (do not merge schema into it)
                        this.patch({
                            zenodoMetadataView: view,
                            zenodoMetadataDraft: this.deepClone(metadataObj),
                        });
                    } else if (!this.state.zenodoMetadataDraft) {
                        // if backend sent only template, start with empty values
                        this.patch({ zenodoMetadataDraft: {} });
                    }

                    // stage (if backend includes it)
                    if (last?.stage) this.changeStage(last.stage);
                },
                error: () =>
                    this.patch({ isLoading: false, errorMessage: 'Failed to infer dataset metadata.' }),
            });
    }



    private improveMetadataOnBackend(datasetName: string) {
        this.patch({ isLoading: true, errorMessage: undefined, selectedAction: 'improve', selectedDatasetName: datasetName });

        this.backend.datasetImproveMetadata(this.state.articleUuid, datasetName, this.state.messages).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                const actions = response?.actions ?? [];
                const msgs = response?.messages ?? response ?? [];

                this.patch({ availableActions: actions });
                this.pushMessages(...msgs);

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;
                const zmRaw = c?.zenodo_metadata;
                if (zmRaw) {
                    this.patch({ zenodoMetadataView: this.buildZenodoMetadataView(zmRaw) });
                }



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
                const c = last?.content ?? last?.contentShort;
                const zmRaw = c?.zenodo_metadata;
                if (zmRaw) {
                    this.patch({ zenodoMetadataView: this.buildZenodoMetadataView(zmRaw) });
                }


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
    private buildZenodoMetadataView(raw: any): ZenodoMetadataView {
        // raw can be:
        //  - { metadata: {...} }
        //  - {...}
        //  - [ { metadata: {...} } ]
        //  - [ {...} ]

        let obj = raw;

        if (Array.isArray(raw)) {
            obj = raw[0] ?? {};
        }

        const m = obj?.metadata ?? obj ?? {};

        return {
            title: m.title ?? '',
            doi: m.doi ?? '',
            publicationDate: m.publication_date ?? m.publicationDate ?? '',

            uploadType: m.upload_type ?? m.uploadType ?? '',
            publicationType: m.publication_type ?? '',
            imageType: m.image_type ?? '',

            accessRight: m.access_right ?? '',
            license: m.license?.id ?? m.license ?? '',
            embargoDate: m.embargo_date ?? '',
            accessConditions: m.access_conditions ?? '',

            version: m.version ?? '',
            language: m.language ?? '',

            creators: (m.creators ?? []).map((c: any) => ({
                name: c.name,
                affiliation: c.affiliation,
                orcid: c.orcid,
                gnd: c.gnd
            })),

            contributors: (m.contributors ?? []).map((c: any) => ({
                name: c.name,
                type: c.type,
                affiliation: c.affiliation,
                orcid: c.orcid,
                gnd: c.gnd
            })),

            keywords: m.keywords ?? [],
            references: m.references ?? [],
            relatedIdentifiers: (m.related_identifiers ?? []).map((r: any) => ({
                identifier: r.identifier,
                relation: r.relation,
                resource_type: r.resource_type
            })),
            communities: (m.communities ?? []).map((x: any) => x.identifier ?? x),
            grants: (m.grants ?? []).map((x: any) => x.id ?? x),

            description: m.description ?? '',

            notes: m.notes ?? '',
            method: m.method ?? '',
            subjects: (m.subjects ?? []).map((s: any) => ({
                term: s.term,
                identifier: s.identifier,
                scheme: s.scheme
            })),
            locations: (m.locations ?? []).map((l: any) => ({
                place: l.place,
                description: l.description,
                lat: l.lat,
                lon: l.lon
            })),
            dates: (m.dates ?? []).map((d: any) => ({
                type: d.type,
                start: d.start,
                end: d.end,
                description: d.description
            })),

            journal: m.journal ?? undefined,
            conference: m.conference ?? undefined,
            imprint: m.imprint ?? undefined,
            partOf: m.part_of ?? undefined,
            thesis: m.thesis ?? undefined,
        };
    }

    private serializeZenodoMetadata(zm: ZenodoMetadataView): any {

        const clean = (obj: any): any => {
            if (!obj || typeof obj !== 'object') return obj;

            const out: any = Array.isArray(obj) ? [] : {};

            Object.entries(obj).forEach(([key, value]) => {
                if (
                    value === undefined ||
                    value === null ||
                    value === '' ||
                    (Array.isArray(value) && value.length === 0)
                ) {
                    return;
                }

                if (typeof value === 'object' && !Array.isArray(value)) {
                    const nested = clean(value);
                    if (nested && Object.keys(nested).length > 0) {
                        out[key] = nested;
                    }
                    return;
                }

                out[key] = value;
            });

            return out;
        };

        const raw = {
            upload_type: zm.uploadType,
            publication_type: zm.publicationType,
            image_type: zm.imageType,

            title: zm.title,
            doi: zm.doi,
            publication_date: zm.publicationDate,

            access_right: zm.accessRight,
            license: zm.license,
            embargo_date: zm.embargoDate,
            access_conditions: zm.accessConditions,

            version: zm.version,
            language: zm.language,

            creators: zm.creators?.map(c => ({
                name: c.name,
                affiliation: c.affiliation,
                orcid: c.orcid,
                gnd: c.gnd
            })),

            contributors: zm.contributors?.map(c => ({
                name: c.name,
                type: c.type,
                affiliation: c.affiliation,
                orcid: c.orcid,
                gnd: c.gnd
            })),

            keywords: zm.keywords,
            references: zm.references,

            related_identifiers: zm.relatedIdentifiers,
            communities: zm.communities,
            grants: zm.grants,

            description: zm.description,

            notes: zm.notes,
            method: zm.method,
            subjects: zm.subjects,
            locations: zm.locations,
            dates: zm.dates,

            journal: zm.journal,
            conference: zm.conference,
            imprint: zm.imprint,
            part_of: zm.partOf,
            thesis: zm.thesis
        };

        return clean(raw);
    }

    private updateMenuSnapshotLists(referenced: string[], nonReferenced: string[]) {
        const menuMessages = [...(this.state.menuMessages ?? [])];
        if (!menuMessages.length) return;

        // Find the last assistant jsonObject menu message (the one with lists/instructions)
        for (let i = menuMessages.length - 1; i >= 0; i--) {
            const m: any = menuMessages[i];
            ifNotice: if (!m?.jsonObject) continue;

            const cShort = m?.contentShort;
            const cFull = m?.content;

            const hasLists =
                cShort && typeof cShort === 'object' &&
                ('referencedDatasets' in cShort || 'nonReferencedDatasets' in cShort);

            if (!hasLists) continue;

            const newMsg = { ...m };
            newMsg.contentShort = { ...(cShort ?? {}), referencedDatasets: referenced, nonReferencedDatasets: nonReferenced };
            newMsg.content = { ...(cFull ?? {}), referencedDatasets: referenced, nonReferencedDatasets: nonReferenced };

            menuMessages[i] = newMsg;
            this.patch({ menuMessages });
            return;
        }
    }

    private deepClone<T>(x: T): T {
        return x == null ? x : JSON.parse(JSON.stringify(x));
    }

    private deepMerge(target: any, source: any): any {
        if (source == null) return target;

        if (Array.isArray(target) && Array.isArray(source)) {
            // prefer source for arrays (user/backend values override template)
            return source;
        }

        if (this.isPlainObject(target) && this.isPlainObject(source)) {
            for (const k of Object.keys(source)) {
                if (k in target) target[k] = this.deepMerge(target[k], source[k]);
                else target[k] = source[k];
            }
            return target;
        }

        // primitives: prefer source
        return source;
    }

    private isPlainObject(v: any): boolean {
        return v != null && typeof v === 'object' && !Array.isArray(v);
    }
    setZenodoDraft(draft: any) {
        this.patch({ zenodoMetadataDraft: draft });
    }


}