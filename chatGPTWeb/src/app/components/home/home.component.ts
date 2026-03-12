import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { ReproWorkflowService } from '../../service/repro-workflow/repro-workflow.service';
import { DatasetAnalysisService } from '../../service/dataset-analysis/dataset-analysis.service';
import { BackendService } from '../../service/backend.service';

import { ReproStages, ReproState, ReproFromDoiState } from '../../service/repro-workflow/repro-workflow.types';
import { DataStages, DataState,  } from '../../service/dataset-analysis/dataset-analysis.types';


enum AppStage {
    Start = 'Start',
    Repro = 'Repro',
    Dataset = 'Dataset',
    ReproFromDoi = 'ReproFromDoi'
}

/** JSON keys that should NOT be displayed as labels */
const HIDDEN_JSON_KEYS: readonly string[] = [
    'fuji_summary',
    'zenodo_metadata',
];

const HIDDEN_ROW_KEYS: readonly string[] = [
    'action',
    'template',
    'zenodo_status',
];

@Component({
    selector: 'app-home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.css', '../../app.component.css']
})
export class HomeComponent {
    protected readonly Array = Array;

    // App stage (UI-level)
    appStages = AppStage;
    appStage: AppStage = AppStage.Start;
    zenodoDraftText: string = '';
    metadataJsonError: string = '';


    // Uploads (separados)
    fileToUploadRepro: File | null = null;
    private fileToUploadPdf: File | null = null;

    // Data Extension Layer
    useDataLayer = false;
    dataMode: 'file' | 'doi' = 'file';
    fileToUploadData: File | null = null;
    datasetDoi = '';

    // Auth
    password: string = '';
    isAuthenticated: boolean = true;
    errorMessage: any;

    // Expor enums para o template (se precisares)
    reproStages = ReproStages;
    dataStages = DataStages;

    // Input do chat
    userMessage: string = '';

    // Reproduce from Artifact DOI
    artifactDoiInput: string = '';
    reproFromDoiState: ReproFromDoiState = { phase: 'idle' };
    private _reproFromDoiPollId?: number;

    // Active state for the template (switches between Repro and Dataset)
    state$: Observable<ReproState | DataState>;

    constructor(
        public workflow: ReproWorkflowService,
        public analysis: DatasetAnalysisService,
        private backend: BackendService
    ) {
        // default (Start screen only needs isLoading/error/messages, so any state works)
        this.state$ = this.workflow.state$;
    }

    isDataState(s: ReproState | DataState): s is DataState {
        return (s as DataState).articleUuid !== undefined;
    }

    /** Helper for template */
    shouldDisplayKey(key: string): boolean {
        return !HIDDEN_JSON_KEYS.includes(key);
    }

    shouldDisplayRow(key: string): boolean {
        return !HIDDEN_ROW_KEYS.includes(key);
    }

    /** Helpers do template (json rendering) */
    objectKeys(obj: any): string[] {
        return Object.keys(obj);
    }

    isObject(value: any): boolean {
        return value && typeof value === 'object' && !Array.isArray(value);
    }

    /** Enviar mensagem (enter/click) */
    sendMessage() {
        // If Dataset + an action form is active, submit it and stop.
        if (this.appStage === AppStage.Dataset) {
            const didSubmit = this.analysis.submitActionForm?.(); // return boolean
            if (didSubmit) {
                this.userMessage = '';
                return;
            }
        }

        const text = (this.userMessage ?? '').trim();
        if (!text) return;

        if (this.appStage === AppStage.Repro) {
            this.workflow.sendUserMessage(text);
        } else if (this.appStage === AppStage.Dataset) {
            this.analysis.sendUserMessage(text);
        }

        this.userMessage = '';
    }

    onSaveZenodoMetadata(cleaned: any) {
        const zenodoToken = undefined;
        this.analysis.saveOrCreateZenodo(cleaned, zenodoToken);   // ✅
    }


    /** Upload (REPRO) */
    onFileChangeRepro(event: any) {
        const file = event?.target?.files?.[0];
        this.fileToUploadRepro = file ?? null;
        if (this.fileToUploadRepro) console.log('Accepted repro file:', this.fileToUploadRepro.name);
    }

    onFileChangeData(event: any) {
        const file = event?.target?.files?.[0];
        this.fileToUploadData = file ?? null;
    }

    onSubmitRepro() {
        if (!this.fileToUploadRepro) return;

        const formData = new FormData();
        formData.append('file', this.fileToUploadRepro);

        if (this.useDataLayer) {
            formData.append('use_data_layer', 'true');
            if (this.dataMode === 'file' && this.fileToUploadData) {
                formData.append('data_file', this.fileToUploadData);
            } else if (this.dataMode === 'doi' && this.datasetDoi.trim()) {
                formData.append('dataset_doi', this.datasetDoi.trim());
            }
        }

        this.appStage = AppStage.Repro;
        this.state$ = this.workflow.state$;

        this.workflow.uploadProject(formData);
    }

    /** Upload (PDF Dataset Analysis) */
    onFileChangePdf(event: any) {
        const file = event?.target?.files?.[0];
        this.fileToUploadPdf = file ?? null;
        if (this.fileToUploadPdf) console.log('Accepted PDF file:', this.fileToUploadPdf.name);
    }

    onSubmitDataset() {
        if (!this.fileToUploadPdf) return;

        const formData = new FormData();
        formData.append('file', this.fileToUploadPdf);

        this.appStage = AppStage.Dataset;
        this.state$ = this.analysis.state$;

        this.analysis.findInformationArticle(formData);
    }

    /** Password */
    onSubmitpass() {
        this.isAuthenticated = true;
        this.errorMessage = '';
    }
    onDatasetActionClick(action: string) {
        if (this.appStage !== AppStage.Dataset) return;
        this.analysis.selectAction(action);
    }



    /** Examples toggle */
    examplesVisibility: { [key: string]: boolean } = {};

    toggleExamples(message: any): void {
        const messageId = message.id || message.contentShort;
        this.examplesVisibility[messageId] = !this.examplesVisibility[messageId];
    }

    isExamplesVisible(message: any): boolean {
        // If there are no examples, never show the section
        if (!message?.examples || !String(message.examples).trim()) return false;

        const messageId = message.id || message.contentShort;
        return !!this.examplesVisibility[messageId];
    }

    isZenodoKey(key: string): boolean {
        return key === 'zenodo_metadata'
            || key === 'zenodo_metadata_template'
            || key === 'zenodoMetadata';
    }



    getOutputFileUrl(filename: string): string {
        const uuid = this.reproFromDoiState.newProjectUuid ?? '';
        return this.backend.getOutputFileUrl(uuid, filename);
    }

    onReproduceFromDoi() {
        const doi = this.artifactDoiInput.trim();
        if (!doi) return;

        this.appStage = AppStage.ReproFromDoi;
        this.reproFromDoiState = { phase: 'init' };

        // Step 1: init (resolve DOI, download & extract zip)
        this.backend.reproduceFromDoiInit(doi).subscribe({
            next: (res: any) => {
                const newUuid = res?.new_project_uuid;
                if (!newUuid) {
                    this.reproFromDoiState = { phase: 'error', errorMessage: 'Init failed: no project UUID returned.' };
                    return;
                }
                this.reproFromDoiState = { phase: 'running', newProjectUuid: newUuid };

                // Start polling run-progress
                this._reproFromDoiPollId = window.setInterval(() => {
                    this.backend.getRunProgress(newUuid).subscribe({
                        next: (p: any) => {
                            if (p?.detail) {
                                this.reproFromDoiState = { ...this.reproFromDoiState, runProgressDetail: p.detail };
                            }
                        }
                    });
                }, 2000);

                // Step 2: run experiment
                this.backend.reproduceRun(newUuid).subscribe({
                    next: (response: any) => {
                        window.clearInterval(this._reproFromDoiPollId);
                        const last = response?.[response.length - 1];
                        const c = last?.content ?? {};
                        this.reproFromDoiState = {
                            phase: 'completed',
                            newProjectUuid: newUuid,
                            logs: typeof c === 'string' ? c : c.logs ?? last?.contentShort,
                            outputFiles: c.output_files ?? [],
                            commandToRun: c.command_to_run,
                            dataStrategy: c.data_strategy,
                        };
                    },
                    error: (err: any) => {
                        window.clearInterval(this._reproFromDoiPollId);
                        this.reproFromDoiState = {
                            phase: 'error',
                            newProjectUuid: newUuid,
                            errorMessage: `Experiment run failed (HTTP ${err?.status})`,
                        };
                    }
                });
            },
            error: (err: any) => {
                this.reproFromDoiState = {
                    phase: 'error',
                    errorMessage: err?.error?.error || `Init failed (HTTP ${err?.status})`,
                };
            }
        });
    }

    goToAppStart(resetWorkflows: boolean = false) {
        this.appStage = this.appStages.Start;
        this.userMessage = '';
        this.state$ = this.workflow.state$; // pick one so template stays stable

        if (resetWorkflows) {
            this.workflow.reset();
            this.analysis.reset?.();
        }
    }

    fairLabel(k: string): string {
        switch (k) {
            case 'F': return 'Findable';
            case 'A': return 'Accessible';
            case 'I': return 'Interoperable';
            case 'R': return 'Reusable';
            case 'FAIR': return 'FAIR';
            default: return k;
        }
    }

    getFairRows(scoreByElement: any): Array<{ key: string; label: string; earned: any; total: any; percent: any; missing: any }> {
        if (!scoreByElement || typeof scoreByElement !== 'object') return [];
        const order = ['F', 'A', 'I', 'R', 'FAIR'];
        return order
            .filter(k => scoreByElement[k])
            .map(k => ({
                key: k,
                label: this.fairLabel(k),
                earned: scoreByElement[k]?.earned,
                total: scoreByElement[k]?.total,
                percent: scoreByElement[k]?.percent,
                missing: scoreByElement[k]?.missing
            }));
    }

    hasFujiSummary(obj: any): boolean {
        return !!obj?.score_by_element;
    }

    warningDimsOrder(): string[] {
        return ['findable', 'accessible', 'interoperable', 'reusable'];
    }

    warningDimLabel(dim: string): string {
        switch (dim) {
            case 'findable': return 'Findable';
            case 'accessible': return 'Accessible';
            case 'interoperable': return 'Interoperable';
            case 'reusable': return 'Reusable';
            default: return dim;
        }
    }
    maturityLabel(value: number | null | undefined): string {
        if (value == null) return 'Unknown';

        if (value < 0.5) return 'Incomplete';
        if (value >= 0.5 && value < 1.5) return 'Initial';
        if (value >= 1.5 && value < 2.5) return 'Moderate';
        if (value > 2.5 && value <= 3) return 'Advanced';

        return 'Unknown';
    }

    loadDraftToText(s: any) {
        this.metadataJsonError = '';
        try {
            this.zenodoDraftText = JSON.stringify(s.zenodoMetadataDraft ?? {}, null, 2);
        } catch {
            this.zenodoDraftText = '';
        }
    }

    applyTextToDraft() {
        this.metadataJsonError = '';
        try {
            const parsed = JSON.parse(this.zenodoDraftText || '{}');
            this.analysis.setZenodoDraft(parsed); // ✅ add this method in service (next step)
        } catch (e: any) {
            this.metadataJsonError = 'Invalid JSON: ' + (e?.message ?? '');
        }
    }

    saveMetadataAndReturnToMenu() {
        // ensure draft in service matches text (if user forgot to click apply)
        this.applyTextToDraft();
        if (this.metadataJsonError) return;

        this.analysis.saveEditedMetadata(); // your existing function (we’ll improve it)
        this.analysis.selectAction('go to menu'); // back to menu
    }

    cancelMetadataEdit() {
        this.metadataJsonError = '';
        this.analysis.selectAction('go to menu');
    }

    onCreateFilesChange(event: any) {
        const files: File[] = Array.from(event?.target?.files ?? []);
        this.analysis.setCreateFiles(files);
    }

    onToggleReplaceFiles(event: any) {
        const checked = !!event?.target?.checked;
        this.analysis.setReplaceFilesMode(checked);
    }




}
