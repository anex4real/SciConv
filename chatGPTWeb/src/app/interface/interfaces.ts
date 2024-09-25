export interface ContainerElement {
    containerId: number;
    status: string;
    action?: string;
}


export class FileItem {
    name: string | undefined;
    isDirectory?: boolean | undefined;
    size?: number;
    __KEY__?: string;
    items?: FileItem[];
    dateModified?: string;
}

export interface DockerConfiguration {
    configurationName: string;
    dockerImageID: string;
    operatingSystem: string;
    port?: number;
    database: {
        dbName?: string;
        dbPort?: string;
        configurationName?: string;
        dockerImageID?: string;
        dbnameConnection?: string;
    } | null;
}

export interface DockerConfigurations {
    [key: string]: DockerConfiguration;
}

export interface Message {
    jsonObject: any
    role: string;
    content: any;
    contentShort: any;
    stage?:any
    examples?: any,
    projectUuid?: any
}

export interface ProjectConfiguration {
    PL: string;
    PLVersion: string;
    Dependencies: string;
    DependenciesVersion: string;

}