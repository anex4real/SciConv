// src/app/service/dataset-analysis/dataset-analysis.service.ts
import {Injectable} from '@angular/core';
import {BehaviorSubject} from 'rxjs';

import {BackendService} from '../backend.service';
import {Message} from '../../interface/interfaces';
import {DataState, DataStages, ZenodoMetadataView} from './dataset-analysis.types';

@Injectable({providedIn: 'root'})
export class DatasetAnalysisService {

    constructor(private backend: BackendService) {}

    private readonly initialState: DataState = {
        /* ===== Core workflow ===== */
        stage: DataStages.FindInformation,
        role: 'user',
        articleUuid: '',

        /* ===== Chat ===== */
        messages: [],
        messageToAsk: undefined,
        examplesToAsk: undefined,
        stageAfterChat: undefined,

        /* ===== Dataset lists ===== */
        referencedDatasets: [],
        nonReferencedDatasets: [],

        /* ===== Active / selected dataset ===== */
        selectedAction: undefined,
        selectedDatasetName: undefined,

        /* ===== UI actions & inputs ===== */
        uiAction: undefined,
        uiListKind: undefined,
        uiDatasetName: undefined,
        uiZenodoRef: undefined,
        uiNewDatasetName: undefined,
        uiInstructions: undefined,

        /* ===== Zenodo metadata ===== */
        zenodoMetadataView: undefined,
        zenodoTemplate: undefined,
        zenodoMetadataDraft: undefined,
        depositionIdsByKey: {},
        activeDepositionKey: undefined,


        /* ===== Backend-driven actions ===== */
        availableActions: [],

        /* ===== UI state ===== */
        isLoading: false,
        errorMessage: undefined,

        /* ===== Navigation ===== */
        GO_BACK_NUMBER: 3,
        goBack: 3,
    };

    private readonly stateSubject = new BehaviorSubject<DataState>(this.initialState);

    readonly state$ = this.stateSubject.asObservable();

    private get state(): DataState {
        return this.stateSubject.value;
    }

    private patch(p: Partial<DataState>) {
        this.stateSubject.next({...this.state, ...p});
    }

    private pushMessages(...msgs: Message[]) {
        this.patch({messages: [...this.state.messages, ...msgs]});
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

    private deepClone<T>(x: T): T {
        return x == null ? x : JSON.parse(JSON.stringify(x));
    }

    private clearUiActionForm() {
        this.patch({
            uiAction: undefined,
            uiListKind: undefined,
            uiDatasetName: undefined,
            uiZenodoRef: undefined,
            uiNewDatasetName: undefined,

            // ✅ create-specific
            uiCreateFiles: undefined,
            uiReplaceFiles: undefined,
        });
    }


    private patchLists(referenced: string[], nonReferenced: string[]) {
        this.patch({referencedDatasets: referenced, nonReferencedDatasets: nonReferenced});
    }

    private goToMenu() {
        const menuActions = this.state.menuActions ?? [];
        const rebuiltMenuMessages = this.rebuildMenuMessagesWithCurrentLists();

        this.patch({
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

    setZenodoDraft(draft: any) {
        this.patch({zenodoMetadataDraft: draft});
    }

    reset() {
        this.stateSubject.next(this.initialState);
    }

    /** ========= 1) Upload PDF -> FindInformation ========= */
    findInformationArticle(formData: FormData) {
        this.patch({isLoading: true, errorMessage: undefined});

        this.backend.uploadArticleFindInformation(formData).subscribe({
            next: (response: any) => {
                this.patch({isLoading: false});

                const articleUuid = response?.article_uuid;
                if (articleUuid) this.patch({articleUuid});

                const actions = response?.actions ?? [];
                this.patch({availableActions: actions, menuActions: actions});

                const msgs = response?.messages ?? [];
                this.pushMessages(...msgs);

                this.patch({menuMessages: msgs});

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;

                if (c?.instructions) this.patch({uiInstructions: c.instructions});

                if (last?.content?.articleUuid) this.patch({articleUuid: last.content.articleUuid});
                if (last?.content?.referencedDatasets) this.patch({referencedDatasets: last.content.referencedDatasets});
                if (last?.content?.nonReferencedDatasets) this.patch({nonReferencedDatasets: last.content.nonReferencedDatasets});

                if (last?.stage)
                    this.patch({stage: last.stage});
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
    }

    saveEditedMetadata() {
        const draft = this.state.zenodoMetadataDraft;
        const template = this.state.zenodoTemplate;

        if (!draft) {
            this.patch({errorMessage: 'Missing metadata draft.'});
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
                this.patch({errorMessage: 'No metadata/template available. Please run infer or improve first.'});
                return true;
            }
            // ✅ ensure editor is bound to the correct deposition “slot”
            if (!this.state.activeDepositionKey) {
                const fallback = (this.state.activeDatasetName || this.state.uiDatasetName || '').trim();
                if (fallback) this.patch({ activeDepositionKey: fallback });
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
            this.patch({ activeDepositionKey: datasetName }); // ✅


            const files = this.state.uiCreateFiles ?? [];
            const replace = !!this.state.uiReplaceFiles;

            this.createRepositoryOnBackend(datasetName, files, replace);

            this.clearUiActionForm();
            this.patch({ activeDatasetName: undefined });
            return true;
        }


        // ---------- INFER (backend) ----------
        if (a === 'infer') {
            const name = (this.state.uiDatasetName || '').trim();

            if (!name) {
                this.patch({errorMessage: 'Please select a dataset from the non-referenced list.'});
                return true;
            }
            this.patch({
                activeDatasetName: name,
                activeDepositionKey: name,   // ✅ key for this dataset
            });
            this.inferMetadataOnBackend(name);
            this.clearUiActionForm();
            return true;
        }

        // ---------- IMPROVE (backend) ----------
        if (a === 'improve') {
            const name = (this.state.uiDatasetName || '').trim();

            if (!name) {
                this.patch({errorMessage: 'Please select a dataset from the referenced list.'});
                return true;
            }

            const entry = (this.state.referencedDatasets ?? []).find(e =>
                this.refEntryName(e).toLowerCase() === name.toLowerCase()
            );

            const doiOrUrl = entry ? this.refEntryLink(entry) : '';
            this.patch({ activeDepositionKey: doiOrUrl || name }); // ✅


            if (!doiOrUrl) {
                this.patch({errorMessage: 'Could not find Zenodo DOI/URL for the selected dataset.'});
                return true;
            }

            console.log('Sending DOI/URL:', doiOrUrl);
            this.getMetadataOnBackend(doiOrUrl); // send DOI/URL
            this.clearUiActionForm();
            return true;
        }

        // ---------- ADD / DELETE / UPDATE (LOCAL) ----------
        const listKind = this.state.uiListKind;
        if (!listKind) {
            this.patch({errorMessage: 'Please select referenced or non-referenced list.'});
            return true;
        }

        const referenced = [...(this.state.referencedDatasets ?? [])];
        const nonReferenced = [...(this.state.nonReferencedDatasets ?? [])];

        // ---------- ADD ----------
        if (a === 'add') {
            const name = (this.state.uiDatasetName || '').trim();
            if (!name) {
                this.patch({errorMessage: 'Please type the dataset name to add.'});
                return true;
            }

            if (listKind === 'non-referenced') {
                const exists = nonReferenced.some(d => d.toLowerCase() === name.toLowerCase());
                if (exists) {
                    this.patch({errorMessage: 'This dataset already exists in non-referenced list.'});
                    return true;
                }

                nonReferenced.push(name);
                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({action: 'add', list: 'referenced', added: name}, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced add: need name + ref
            const ref = (this.state.uiZenodoRef || '').trim();
            if (!ref) {
                this.patch({errorMessage: 'Please provide Zenodo DOI/URL.'});
                return true;
            }

            const exists = referenced.some(e => this.refEntryName(e).toLowerCase() === name.toLowerCase());
            if (exists) {
                this.patch({errorMessage: 'This dataset already exists in referenced list.'});
                return true;
            }

            const entry = this.buildRefEntry(name, ref);
            referenced.push(entry);
            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({action: 'add', list: 'non-referenced', added: name}, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        // ---------- DELETE ----------
        if (a === 'delete') {
            const name = (this.state.uiDatasetName || '').trim();
            if (!name) {
                this.patch({errorMessage: 'Please choose a dataset to delete.'});
                return true;
            }

            if (listKind === 'non-referenced') {
                const idx = nonReferenced.findIndex(d => d.toLowerCase() === name.toLowerCase());
                if (idx < 0) {
                    this.patch({errorMessage: 'Dataset not found in non-referenced list.'});
                    return true;
                }

                const deleted = nonReferenced[idx];
                nonReferenced.splice(idx, 1);
                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({
                    action: 'delete',
                    list: 'non-referenced',
                    deleted
                }, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced delete by dataset name (left side)
            const idx = referenced.findIndex(e => this.refEntryName(e).toLowerCase() === name.toLowerCase());
            if (idx < 0) {
                this.patch({errorMessage: 'Dataset not found in referenced list.'});
                return true;
            }

            const deleted = referenced[idx];
            referenced.splice(idx, 1);
            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({action: 'delete', list: 'referenced', deleted}, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        // ---------- UPDATE ----------
        if (a === 'update') {
            const oldName = (this.state.uiDatasetName || '').trim();
            if (!oldName) {
                this.patch({errorMessage: 'Please choose a dataset to update.'});
                return true;
            }

            const newName = (this.state.uiNewDatasetName || '').trim();
            const newRef = (this.state.uiZenodoRef || '').trim();

            if (!newName && !newRef) {
                this.patch({errorMessage: 'Please edit at least one field (new name and/or Zenodo ref).'});
                return true;
            }

            if (listKind === 'non-referenced') {
                const idx = nonReferenced.findIndex(d => d.toLowerCase() === oldName.toLowerCase());
                if (idx < 0) {
                    this.patch({errorMessage: 'Dataset not found in non-referenced list.'});
                    return true;
                }

                const finalName = newName || nonReferenced[idx];

                // prevent duplicates (other than itself)
                const dup = nonReferenced.some((d, i) =>
                    i !== idx && d.toLowerCase() === finalName.toLowerCase()
                );
                if (dup) {
                    this.patch({errorMessage: 'Another dataset already has that name.'});
                    return true;
                }

                const before = nonReferenced[idx];
                nonReferenced[idx] = finalName;

                this.patchLists(referenced, nonReferenced);
                this.pushLocalEditMessage({
                    action: 'update',
                    list: 'non-referenced',
                    from: before,
                    to: finalName
                }, referenced, nonReferenced);
                this.clearUiActionForm();
                return true;
            }

            // referenced update
            const idx = referenced.findIndex(e => this.refEntryName(e).toLowerCase() === oldName.toLowerCase());
            if (idx < 0) {
                this.patch({errorMessage: 'Dataset not found in referenced list.'});
                return true;
            }

            const before = referenced[idx];
            const oldLink = this.refEntryLink(before);

            const finalName = newName || this.refEntryName(before);
            const finalLink = newRef || oldLink;

            if (!finalLink) {
                this.patch({errorMessage: 'Referenced dataset must have a Zenodo DOI/URL.'});
                return true;
            }

            // prevent duplicates by name (except itself)
            const dup = referenced.some((e, i) =>
                i !== idx && this.refEntryName(e).toLowerCase() === finalName.toLowerCase()
            );
            if (dup) {
                this.patch({errorMessage: 'Another referenced dataset already has that name.'});
                return true;
            }

            const after = this.buildRefEntry(finalName, finalLink);
            referenced[idx] = after;

            this.patchLists(referenced, nonReferenced);
            this.pushLocalEditMessage({
                action: 'update',
                list: 'referenced',
                from: before,
                to: after
            }, referenced, nonReferenced);
            this.clearUiActionForm();
            return true;
        }

        return true;
    }

    setCreateFiles(files: File[]) {
        this.patch({ uiCreateFiles: files ?? [] });
    }

    setReplaceFilesMode(replace: boolean) {
        this.patch({ uiReplaceFiles: !!replace });
    }


    private rebuildMenuMessagesWithCurrentLists(): Message[] {
        const menuMessages = [...(this.state.menuMessages ?? [])];
        if (!menuMessages.length) return menuMessages;

        const instructions = this.state.uiInstructions ?? '';

        // Start from CURRENT state lists
        let referenced = [...(this.state.referencedDatasets ?? [])];
        let nonReferenced = [...(this.state.nonReferencedDatasets ?? [])];


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

        this.patch({menuMessages});
        return menuMessages;
    }

    saveOrCreateZenodo(cleanedMetadata: any, zenodoToken?: string) {
        const articleUuid = this.state.articleUuid;
        if (!articleUuid) {
            this.patch({ errorMessage: 'Missing article UUID.' });
            return;
        }

        const depositionId = this.getActiveDepositionId();

        // ✅ If no deposition id for that key, CREATE instead of failing
        if (!depositionId) {
            this.createRepositoryFromCleanedMetadata(cleanedMetadata, zenodoToken);
            return;
        }

        const formData = new FormData();
        formData.append('metadata', JSON.stringify({ metadata: cleanedMetadata }));
        if (zenodoToken) formData.append('zenodo_token', zenodoToken);
        formData.append('replace_files', 'false');

        this.patch({ isLoading: true, errorMessage: undefined });

        this.backend.datasetEditZenodo(articleUuid, depositionId, formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                const dep = response?.deposition;
                if (dep?.metadata) {
                    this.patch({
                        zenodoMetadataView: this.buildZenodoMetadataView({ metadata: dep.metadata }),
                        zenodoMetadataDraft: this.deepClone(dep.metadata),
                    });
                }

                this.selectAction('go to menu');
            },
            error: () => {
                this.patch({ isLoading: false, errorMessage: 'Failed to edit Zenodo deposition.' });
            }
        });
    }


    private createRepositoryOnBackend(datasetName: string, files: File[] = [], replaceFiles: boolean = false) {
        this.patch({isLoading: true, errorMessage: undefined});

        const zm = this.state.zenodoMetadataView;
        if (!zm) {
            this.patch({isLoading: false, errorMessage: 'No Zenodo metadata available.'});
            return;
        }

        const metadataPayload = {
            metadata: this.serializeZenodoMetadata(zm),
        };

        const formData = new FormData();
        formData.append('metadata', JSON.stringify(metadataPayload));
        formData.append('file_mode', replaceFiles ? 'replace' : 'merge');

        for (const f of (files ?? [])) {
            formData.append('files', f, f.name);
        }


        this.backend.datasetCreateZenodo(this.state.articleUuid, formData).subscribe({
            next: (response: any) => {
                this.patch({isLoading: false});
                const actions = response?.actions ?? [];
                this.patch({availableActions: actions});

                const msgs = response?.messages ?? [];
                this.pushMessages(...msgs);

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;

                const depId = c?.deposition_id;
                if (depId) this.storeDepositionIdForActiveKey(depId);


// ✅ status from backend
                const status = c?.zenodo_status;

// ✅ metadata from backend
                const zm = c?.zenodo_metadata;
                let view
                if (zm) {
                    view = this.buildZenodoMetadataView({ metadata: zm });
                    this.patch({
                        zenodoMetadataView: view,
                        zenodoMetadataDraft: this.deepClone(zm),
                        zenodoStatus: status, // store it
                    });
                }

                // @ts-ignore
                const title = (view.title || '').trim();
                // @ts-ignore
                const doi = (view.doi || '').trim();
                const link = doi ? `https://doi.org/${doi}` : '';

                const originalName = (datasetName || '').trim(); // ✅ the name selected in UI (function param)

                if (originalName && title && link) {
                    const newNonRef = (this.state.nonReferencedDatasets ?? [])
                        .filter(d => d.toLowerCase() !== originalName.toLowerCase());

                    let newRef = [...(this.state.referencedDatasets ?? [])];
                    const entry = `${title} | ${link}`;

                    newRef = newRef.filter(e => this.refEntryLink(e).trim().toLowerCase() !== link.toLowerCase());

                    let idx = newRef.findIndex(e =>
                        this.refEntryName(e).toLowerCase() === originalName.toLowerCase()
                    );

                    if (idx < 0) {
                        idx = newRef.findIndex(e =>
                            this.refEntryName(e).toLowerCase() === title.toLowerCase()
                        );
                    }

                    if (idx >= 0) newRef[idx] = entry;
                    else newRef.push(entry);

                    this.patch({nonReferencedDatasets: newNonRef, referencedDatasets: newRef});

                    // keep menu snapshot in sync
                    this.updateMenuSnapshotLists(newRef, newNonRef);
                }
            },
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

        this.pushMessages({
            role: "user",
            contentShort: text,
            content: text,
            jsonObject: false,
        });

        switch (this.state.stage) {
            case DataStages.InferDatasetMetadata:
                // user forneceu nome do dataset não citado
                this.inferMetadataOnBackend(text);
                break;

            case DataStages.ImproveDatasetMetadata:
                // user forneceu nome do dataset citado
                this.getMetadataOnBackend(text);
                break;
            default:
                break;
        }
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

    private inferMetadataOnBackend(datasetName: string) {
        this.patch({isLoading: true, errorMessage: undefined});

        this.backend
            .datasetInferMetadata(this.state.articleUuid, datasetName, this.state.messages)
            .subscribe({
                next: (response: any) => {
                    this.patch({isLoading: false});

                    const actions = response?.actions ?? [];
                    const msgs = response?.messages ?? [];

                    this.patch({availableActions: actions});
                    this.pushMessages(...msgs);

                    const last = msgs?.[msgs.length - 1];

                    const c = last?.content ?? last?.contentShort;

                    if (c?.instructions) this.patch({uiInstructions: c.instructions});

                    const tplRaw = c?.template;
                    const templateObj = (tplRaw?.metadata ?? tplRaw) ?? undefined;

                    if (templateObj) {
                        this.patch({zenodoTemplate: templateObj});
                    }

                    const zmRaw = c?.zenodo_metadata;

                    if (zmRaw) {
                        const first = Array.isArray(zmRaw) ? (zmRaw[0] ?? {}) : zmRaw;
                        const metadataObj = (first?.metadata ?? first) ?? {};

                        const view = this.buildZenodoMetadataView(zmRaw);

                        this.patch({
                            zenodoMetadataView: view,
                            zenodoMetadataDraft: this.deepClone(metadataObj),
                        });
                    } else if (!this.state.zenodoMetadataDraft) {
                        this.patch({zenodoMetadataDraft: {}});
                    }

                    if (last?.stage) this.patch({stage: last.stage});
                },
                error: () =>
                    this.patch({isLoading: false, errorMessage: 'Failed to infer dataset metadata.'}),
            });
    }

    private getMetadataOnBackend(doiOrUrl: string) {
        this.patch({isLoading: true, errorMessage: undefined, selectedAction: 'improve'});

        console.log(doiOrUrl);
        this.backend.datasetGetMetadata(this.state.articleUuid, doiOrUrl).subscribe({
            next: (response: any) => {
                this.patch({isLoading: false});

                const actions = response?.actions ?? [];
                const msgs = response?.messages ?? [];

                this.patch({availableActions: actions});
                this.pushMessages(...msgs);

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;

                // ✅ 1) template
                const tplRaw = c?.template;
                const templateObj = (tplRaw?.metadata ?? tplRaw) ?? undefined;
                if (templateObj) {
                    this.patch({zenodoTemplate: templateObj});
                }

                // ✅ 2) metadata list -> view + draft
                const zmRaw = c?.zenodo_metadata;
                if (zmRaw) {
                    const first = Array.isArray(zmRaw) ? (zmRaw[0] ?? {}) : zmRaw;
                    const metadataObj = (first?.metadata ?? first) ?? {};

                    this.patch({
                        zenodoMetadataView: this.buildZenodoMetadataView(zmRaw),
                        zenodoMetadataDraft: this.deepClone(metadataObj),
                    });
                } else if (!this.state.zenodoMetadataDraft) {
                    this.patch({zenodoMetadataDraft: {}});
                }

                if (last?.stage) this.patch({stage: last.stage});
            },
            error: () => {
                this.patch({
                    isLoading: false,
                    errorMessage: 'Failed to improve dataset metadata. Please try again.',
                });
            }
        });
    }

    private buildZenodoMetadataView(raw: any): ZenodoMetadataView {
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
            if (!m?.jsonObject) continue;

            const cShort = m?.contentShort;
            const cFull = m?.content;

            const hasLists =
                cShort && typeof cShort === 'object' &&
                ('referencedDatasets' in cShort || 'nonReferencedDatasets' in cShort);

            if (!hasLists) continue;

            const newMsg = {...m};
            newMsg.contentShort = {
                ...(cShort ?? {}),
                referencedDatasets: referenced,
                nonReferencedDatasets: nonReferenced
            };
            newMsg.content = {...(cFull ?? {}), referencedDatasets: referenced, nonReferencedDatasets: nonReferenced};

            menuMessages[i] = newMsg;
            this.patch({menuMessages});
            return;
        }
    }

    private createRepositoryFromCleanedMetadata(cleanedMetadata: any, zenodoToken?: string) {
        const articleUuid = this.state.articleUuid;
        if (!articleUuid) {
            this.patch({ errorMessage: 'Missing article UUID.' });
            return;
        }

        this.patch({ isLoading: true, errorMessage: undefined });

        const formData = new FormData();
        formData.append('metadata', JSON.stringify({ metadata: cleanedMetadata }));

        // keep your file_mode logic if needed:
        const replace = !!this.state.uiReplaceFiles;
        formData.append('file_mode', replace ? 'replace' : 'merge');

        // optional token
        if (zenodoToken) formData.append('zenodo_token', zenodoToken);

        // optional files
        for (const f of (this.state.uiCreateFiles ?? [])) {
            formData.append('files', f, f.name);
        }

        this.backend.datasetCreateZenodo(articleUuid, formData).subscribe({
            next: (response: any) => {
                this.patch({ isLoading: false });

                const actions = response?.actions ?? [];
                this.patch({ availableActions: actions });

                const msgs = response?.messages ?? [];
                this.pushMessages(...msgs);

                const last = msgs?.[msgs.length - 1];
                const c = last?.content ?? last?.contentShort;

                // ✅ store deposition id under current key
                const depId = c?.deposition_id;
                if (depId) this.storeDepositionIdForActiveKey(depId);

                // ✅ status + metadata
                if (c?.zenodo_status) this.patch({ zenodoStatus: c.zenodo_status });

                const zm = c?.zenodo_metadata;
                if (zm) {
                    const view = this.buildZenodoMetadataView({ metadata: zm });
                    this.patch({
                        zenodoMetadataView: view,
                        zenodoMetadataDraft: this.deepClone(zm),
                    });
                }

                this.selectAction('go to menu');
            },
            error: () => {
                this.patch({ isLoading: false, errorMessage: 'Failed to create Zenodo repository.' });
            }
        });
    }

    private getActiveKey(): string {
        return (this.state.activeDepositionKey || this.state.activeDatasetName || '').trim();
    }

    private getActiveDepositionId(): number | undefined {
        const key = this.getActiveKey();
        if (!key) return undefined;
        return this.state.depositionIdsByKey?.[key];
    }

    private storeDepositionIdForActiveKey(depId: number) {
        const key = this.getActiveKey();
        if (!key) return;

        const map = { ...(this.state.depositionIdsByKey ?? {}) };
        map[key] = depId;

        this.patch({ depositionIdsByKey: map });
    }


}