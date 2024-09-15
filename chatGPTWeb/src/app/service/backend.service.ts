import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {Observable} from "rxjs";
import {Message} from "../interface/interfaces";
import {HttpClient} from "@angular/common/http";


@Injectable({
    providedIn: 'root'
})
export class BackendService {
    baseUrl = 'http://localhost:8080';



    constructor(private router: Router,
                private http: HttpClient
    ) {
        //const user: any = localStorage.getItem('user');
        //this.userSubject = new BehaviorSubject<User>(JSON.parse(user));
        //this.user = this.userSubject.asObservable();
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




    findProjectFiles(projectUuid: any): Observable<any> {
        return this.http.get(`${this.baseUrl}/project/${projectUuid}/find_files`);
    }

    findConfigurations(projectUuid: string, filenames: string[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/find-configurations`, {
            filenames: filenames
        });
    }


    BuildDockerFile(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/build-docker-file-chat`, {
            messages: messages
        });

    }

    BuildDockerImage(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/build-docker-image-chat`, {
            messages: messages
        });

    }

    RunContainer(projectUuid: string, dockerImageID: string, commandToRun: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/run-container-chat`, {
            messages: messages,
            dockerImageId: dockerImageID,
            commandToRun: commandToRun
        });

    }

    ResearchArtifact(projectUuid: string, dockerImageID: string, commandToRun: string, messages: Message[]) {
        
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/research-artifact-chat`, {
            messages: messages,
            dockerImageId: dockerImageID,
            commandToRun: commandToRun
        });
    }

    ChatInteraction(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/chat-interation`, {
            messages: messages
        });

    }

    inferFilesToRun(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/infer-files-to-run`, {
            messages: messages
        });
    }

    parametersToUseConfirmation(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/parameters-to-use-confirmation`, {
            messages: messages
        });
    }

    findConfigurationsFunc(projectUuid: string, messages: Message[]) {
        return this.http.post(`${this.baseUrl}/project/${projectUuid}/find-configurations-change`, {
            messages: messages
        });

    }
}