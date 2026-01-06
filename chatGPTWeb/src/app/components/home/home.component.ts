import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { ReproWorkflowService } from '../../service/repro-workflow/repro-workflow.service';
import { DatasetAnalysisService } from '../../service/dataset-analysis/dataset-analysis.service';

import { ReproStages, ReproState } from '../../service/repro-workflow/repro-workflow.types';
import { DataStages, DataState,  } from '../../service/dataset-analysis/dataset-analysis.types';


enum AppStage {
    Start = 'Start',
    Repro = 'Repro',
    Dataset = 'Dataset'
}

/** JSON keys that should NOT be displayed as labels */
const HIDDEN_JSON_KEYS: readonly string[] = [
    'fuji_summary',
    'zenodo_metadata',
];

const HIDDEN_ROW_KEYS: readonly string[] = [
    'action',
    'template'
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
    private fileToUploadRepro: File | null = null;
    private fileToUploadPdf: File | null = null;

    // Auth
    password: string = '';
    isAuthenticated: boolean = true;
    errorMessage: any;

    // Expor enums para o template (se precisares)
    reproStages = ReproStages;
    dataStages = DataStages;

    // Input do chat
    userMessage: string = '';

    // Active state for the template (switches between Repro and Dataset)
    state$: Observable<ReproState | DataState>;

    constructor(
        public workflow: ReproWorkflowService,
        public analysis: DatasetAnalysisService
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
        // if you have a token input in the UI, pass it; otherwise undefined
        const zenodoToken = undefined; // or this.zenodoToken if you store it

        this.analysis.editZenodoOnBackend(cleaned, zenodoToken);
    }



    /** Upload (REPRO) */
    onFileChangeRepro(event: any) {
        const file = event?.target?.files?.[0];
        this.fileToUploadRepro = file ?? null;
        if (this.fileToUploadRepro) console.log('Accepted repro file:', this.fileToUploadRepro.name);
    }

    onSubmitRepro() {
        if (!this.fileToUploadRepro) return;

        const formData = new FormData();
        formData.append('file', this.fileToUploadRepro);

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



}
