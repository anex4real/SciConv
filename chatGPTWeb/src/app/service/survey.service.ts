import {Injectable} from '@angular/core';
import {environment} from "../../environments/environment";
import {Message} from "../interface/interfaces";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";

@Injectable({
    providedIn: 'root',
})

export class SurveyService {
    baseUrl: string = environment.baseUrl;  // Set the baseUrl from environment
    writeToFile: boolean = false;
    writeToFileFinal: boolean = false;
    NUM_SCALES = 6;
    scales = [

        {
            name: 'Mental Demand',
            index: 0,
            left: 'Low',
            right: 'High',
            definition: 'How much mental and perceptual activity was required (e.g. thinking, deciding, calculating, remembering, looking, searching, etc)? Was the task easy or demanding, simple or complex, exacting or forgiving?',
        },
        {
            name: 'Physical Demand',
            index: 1,
            left: 'Low',
            right: 'High',
            definition: 'How much physical activity was required (e.g. pushing, pulling, turning, controlling, activating, etc)? Was the task easy or demanding, slow or brisk, slack or strenuous, restful or laborious?',
        },
        {
            name: 'Temporal Demand',
            index: 2,
            left: 'Low',
            right: 'High',
            definition: 'How much time pressure did you feel due to the rate of pace at which the tasks or task elements occurred? Was the pace slow and leisurely or rapid and frantic?',
        },
        {
            name: 'Performance',
            index: 3,
            left: 'Good',
            right: 'Poor',
            definition: 'How successful do you think you were in accomplishing the goals of the task set by the experimenter (or yourself)? How satisfied were you with your performance in accomplishing these goals?',
        },
        {
            name: 'Effort',
            index: 4,
            left: 'Low',
            right: 'High',
            definition: 'How hard did you have to work (mentally and physically) to accomplish your level of performance?',
        },
        {
            name: 'Frustration',
            index: 5,
            left: 'Low',
            right: 'High',
            definition: 'How insecure, discouraged, irritated, stressed and annoyed versus secure, gratified, content, relaxed and complacent did you feel during the task?',
        },
    ];

    pairings = ['4 3', '2 5', '2 4', '1 5', '3 5', '1 2', '1 3', '2 0', '5 4', '3 0', '3 2', '0 4', '0 1', '4 1', '5 0'];
    pair_num: number = 0;

    resultsRating: number[] = [];
    resultsTally: number[] = new Array(this.NUM_SCALES).fill(0);
    currentPairIndex = 0;

    isScalesCompleted = false;
    results_weight: number[] = [];
    results_overall: number = 0;
    pair1Label: string = '';
    pair2Label: string = '';
    pair1Def: string = '';
    pair2Def: string = '';

    constructor(private http: HttpClient) {
    }

    setRating(index: number, value: any) {
        console.log("aqui")
        this.resultsRating[index] = value;
        console.log(this.resultsRating)
    }

    isPairComparisonFinished(surveyId:any) {
        this.writeToFile = this.currentPairIndex >= this.pairings.length;
        console.log("final")
        console.log(this.writeToFile)
        console.log("finalFinal")
        console.log(this.writeToFileFinal)

        if (this.writeToFile) {
            if (!this.writeToFileFinal) {
                this.calculateResults()
                const dataToSend = {
                    weights: this.results_weight,
                    tally: this.resultsTally,
                    overall: this.results_overall
                };

                // Send data to the server
                this.sendDataToServer(dataToSend, surveyId).subscribe((response: any) => {
                    console.log(response);
                })
                this.writeToFileFinal = true;
            }

        }
        return this.writeToFile
    }

    nextPairComparison() {
        this.currentPairIndex++;
    }

    getCurrentPair() {
        console.log(this.pairings[this.currentPairIndex].split(' ').map(Number))
        return this.pairings[this.currentPairIndex].split(' ').map(Number);
    }
    getScales() {
        return this.scales
    }

    tallyResult(choice: number) {
        this.resultsTally[choice]++;
        this.nextPairComparison();
    }

    areScalesCompleted() {


        const nullElements = this.resultsRating.filter(element => element === null);

        if (nullElements.length > 0) {
            console.log(`The array contains ${nullElements.length} null element(s).`);
            return false
        } else {
            console.log('The array does not contain any null elements.');
            return true
        }


    }


    setPairLabels() {
        const indexes = this.pairings[this.pair_num].split(' ');
        this.pair1Label = this.scales[parseInt(indexes[0])].name;
        this.pair2Label = this.scales[parseInt(indexes[1])].name;
        // @ts-ignore
        this.pair1Def = this.scales[parseInt(indexes[0])].description;
        // @ts-ignore
        this.pair2Def = this.scales[parseInt(indexes[1])].description;
    }


    // nextPair() {
    //     this.pair_num++;
    //     if (this.pair_num >= this.pairings.length) {
    //         this.part3 = false;
    //         this.part4 = true;
    //         this.calculateResults();
    //     } else {
    //         this.setPairLabels();
    //     }
    // }

    calculateResults() {
        this.results_overall = 0;
        for (let i = 0; i < this.NUM_SCALES; i++) {
            this.results_weight[i] = this.resultsTally[i] / 15.0;
            this.results_overall += this.results_weight[i] * this.resultsRating[i];
        }
        console.log("Weight")
        console.log(this.results_weight)

        console.log("times")
        console.log(this.resultsTally)

        console.log("results_overall")
        console.log(this.results_overall)
        // Prepare data to send to the server



    }

    sendDataToServer(dataToSend: any, surveyId:any): Observable<any> {
        console.log("send")
        return this.http.post(`${this.baseUrl}/${surveyId}/nasa`, dataToSend);

    }


    finalizeResults() {
        // Calculate weighted results (optional depending on how you want to display results)
    }

    getWriteToFileFinal() {
        return this.writeToFileFinal
    }
}
