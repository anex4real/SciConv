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


    /*    public async chat(message: string): Promise<string> {
            try {

                // Use chatgpt.query method with optional parameters
                const response = await this.chatgpt.query(message, {temperature: 0.8, max_tokens: 32});
                // Return the response text
                return response.text;
            } catch (error) {
                // Handle any errors
                console.error(error);
                return 'Something went wrong.';
            }
        }*/

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
}