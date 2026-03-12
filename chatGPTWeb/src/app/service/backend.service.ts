import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {Observable} from "rxjs";
import {Message} from "../interface/interfaces";
import {HttpClient} from "@angular/common/http";
import {environment} from "../../environments/environment";


@Injectable({
    providedIn: 'root'
})
export class BackendService {
    //baseUrl = 'http://localhost:8080';
    //baseUrl = 'http://backend:8080';
    baseUrl: string = environment.baseUrl;  // Set the baseUrl from environment
    private mySecretToken: string;
    private headers: { Authorization: string };


    constructor(private router: Router,
                private http: HttpClient
    ) {
        //const user: any = localStorage.getItem('user');
        //this.userSubject = new BehaviorSubject<User>(JSON.parse(user));
        //this.user = this.userSubject.asObservable();
        console.log(this.baseUrl);
        this.mySecretToken = 'my-secret-token'
        this.headers = {
            Authorization: 'Bearer ' + this.mySecretToken
        };

        this.getServerHome().subscribe((response: any) => {
            console.log(response)
            console.log("successful server connection")
        })
    }


    private password = 'lazaro2024'; // Replace with your desired password

    // Method to validate the password
    validatePassword(inputPassword: string): boolean {
        return inputPassword === this.password;
    }


    getServerHome() {
        console.log("link:" + `${this.baseUrl}/`)
        return this.http.get(`${this.baseUrl}/`);
    }


    findProjectFiles(projectUuid: any): Observable<any> {
        return this.http.post(
            `${this.baseUrl}/project/find_files`,
            {possibleProjectUuid: projectUuid},
            {headers: this.headers}
        );
    }

    findConfigurations(projectUuid: string, filenames: string[], commandToRun: any) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/find-configurations`, {
                filenames: filenames,
                commandToRun: commandToRun
            },
            {headers: this.headers});
    }


    BuildDockerFile(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/build-docker-file-chat`, {
                messages: messages
            },
            {headers: this.headers});
    }

    BuildDockerImage(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/build-docker-image-chat`, {
                messages: messages
            },
            {headers: this.headers});
    }

    RunContainer(projectUuid: string, dockerImageID: string, commandToRun: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/run-container-chat`, {
                messages: messages,
                dockerImageId: dockerImageID,
                commandToRun: commandToRun
            },
            {headers: this.headers});
    }

    ResearchArtifact(projectUuid: string, dockerImageID: string, commandToRun: string, messages: Message[]) {

        return this.http.post(`${this.baseUrl}/project/${projectUuid}/research-artifact-chat`, {
                messages: messages,
                dockerImageId: dockerImageID,
                commandToRun: commandToRun
            },
            {headers: this.headers});
    }

    ChatInteraction(projectUuid: string, messages: Message[], nextStep: any) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/chat-interation`, {
                messages: messages,
                nextStep: nextStep
            },
            {headers: this.headers});
    }

    inferFilesToRun(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/infer-files-to-run`, {
                messages: messages
            },
            {headers: this.headers});
    }

    parametersToUseConfirmation(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/parameters-to-use-confirmation`, {
                messages: messages
            },
            {headers: this.headers});
    }

    specifyOutputs(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/specify-outputs`, {
                messages: messages
            },
            {headers: this.headers});
    }

    skipOutputs(projectUuid: string) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/specify-outputs`, {
                skip: true
            },
            {headers: this.headers});
    }

    getRunProgress(projectUuid: string) {
        return this.http.get(`${this.baseUrl}/project/${projectUuid}/run-progress`,
            {headers: this.headers});
    }

    uploadArtifactToZenodo(projectUuid: string, body: any = {}) {
        return this.http.post(
            `${this.baseUrl}/project/${projectUuid}/upload-artifact-to-zenodo`,
            body, {headers: this.headers});
    }

    reproduceFromDoiInit(artifactDoi: string) {
        return this.http.post(
            `${this.baseUrl}/project/reproduce-from-doi/init`,
            {artifact_doi: artifactDoi}, {headers: this.headers});
    }

    reproduceRun(newProjectUuid: string) {
        return this.http.post(
            `${this.baseUrl}/project/${newProjectUuid}/reproduce-run`,
            {}, {headers: this.headers});
    }

    getOutputFileUrl(projectUuid: string, filename: string): string {
        return `${this.baseUrl}/project/${projectUuid}/download-output/${filename}`;
    }

    findConfigurationsFunc(projectUuid: string, messages: Message[], myMessage: any) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/find-configurations-change`, {
                messages: messages,
                myMessage: myMessage
            },
            {headers: this.headers});
    }

    uploadProject(formData: FormData) {
        return this.http.post(`${this.baseUrl}/project/upload-project`, formData,
            {headers: this.headers});
    }

    externalizeData(projectUuid: string) {
        return this.http.post(
            `${this.baseUrl}/project/${projectUuid}/externalize-data`,
            {},
            {headers: this.headers}
        );
    }

    uploadArticleFindInformation(formData: FormData) {
        return this.http.post(`${this.baseUrl}/article/upload-file`, formData,
            {headers: this.headers});
    }


// Infer metadata for a NON-referenced dataset (user provides datasetName)
    datasetInferMetadata(projectUuid: string, datasetName: string, messages: Message[]) {
        return this.http.post(
            `${this.baseUrl}/article/${projectUuid}/infer-metadata`,
            {datasetName, messages},
            {headers: this.headers}
        );
    }

// Improve metadata for a REFERENCED dataset
// datasetName here should actually be the DOI / Zenodo URL
    datasetGetMetadata(projectUuid: string, doi: string) {
        return this.http.get(`${this.baseUrl}/article/${projectUuid}/metadata`, {
            headers: this.headers,
            params: { doi }
        });
    }

    datasetCreateZenodo(projectUuid: string, formData: FormData) {
        return this.http.post(
            `${this.baseUrl}/article/${projectUuid}/create-dataset-zenodo`,
            formData,
            { headers: this.headers }
        );
    }

    datasetEditZenodo(articleUuid: string, depositionId: number, formData: FormData) {
        return this.http.post(
            `${this.baseUrl}/article/${articleUuid}/zenodo/${depositionId}/edit`,
            formData,
            { headers: this.headers }
        );
    }






}