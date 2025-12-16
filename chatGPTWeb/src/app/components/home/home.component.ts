import { Component } from '@angular/core';
import { Observable } from 'rxjs';

import { ReproWorkflowService } from '../../service/repro-workflow/repro-workflow.service';
import { DatasetAnalysisService } from '../../service/dataset-analysis/dataset-analysis.service';

import { ReproStages, ReproState } from '../../service/repro-workflow/repro-workflow.types';
import { DataStages, DataState } from '../../service/dataset-analysis/dataset-analysis.types';

enum AppStage {
    Start = 'Start',
    Repro = 'Repro',
    Dataset = 'Dataset'
}

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

    /** Helpers do template (json rendering) */
    objectKeys(obj: any): string[] {
        return Object.keys(obj);
    }

    isObject(value: any): boolean {
        return value && typeof value === 'object' && !Array.isArray(value);
    }

    /** Enviar mensagem (enter/click) */
    sendMessage() {
        const text = (this.userMessage ?? '').trim();
        if (!text) return;

        if (this.appStage === AppStage.Repro) {
            this.workflow.sendUserMessage(text);
        } else if (this.appStage === AppStage.Dataset) {
            this.analysis.sendUserMessage(text);
        }

        this.userMessage = '';
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

    /** Examples toggle */
    examplesVisibility: { [key: string]: boolean } = {};

    toggleExamples(message: any): void {
        const messageId = message.id || message.contentShort;
        this.examplesVisibility[messageId] = !this.examplesVisibility[messageId];
    }

    isExamplesVisible(message: any): boolean {
        const messageId = message.id || message.contentShort;
        return !!this.examplesVisibility[messageId];
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
}
