export interface Message {
    jsonObject: any
    role: string;
    content: any;
    contentShort: any;
    stage?:any;
    examples?: any;
    projectUuid?: any;
    goBack?:any
}
