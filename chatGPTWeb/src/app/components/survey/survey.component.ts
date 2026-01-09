import {Component, EventEmitter, Input, Output} from '@angular/core';
import {SurveyService} from "../../service/survey/survey.service";
import {ActivatedRoute} from "@angular/router";

@Component({
    selector: 'app-survey',
    templateUrl: './survey.component.html',
    styleUrls: ['./survey.component.css', '../../app.component.css']
})
export class SurveyComponent {
    surveyId: string = ''

    constructor(public surveyService: SurveyService,
                private route: ActivatedRoute) {
        this.route.params.subscribe(params => {
            this.surveyId = params['id'];
            // @ts-ignore
            if (this.surveyId != "sciconv" && this.surveyId != "codeocean") {
                alert('Survey ID:' + this.surveyId);
            }
            // You can now use this.surveyId to fetch survey data or perform other logic
        });
        for (let i = 0; i < 6; i++) {
            this.surveyService.setRating(i, null);
        }
        this.surveyScales = this.surveyService.getScales()
    }


    startTask2: boolean = false

    nextStep() {
        if (this.surveyService.areScalesCompleted()) {
            this.surveyService.isScalesCompleted = true;
        } else {
            alert('Please complete all scales!');
        }
    }

    nextStep2() {
        if (this.surveyService.areScalesCompleted()) {
            this.startTask2 = true

        }
    }

    surveyScales: any



    // Current value of the slider
    currentValue: number = -1;

    // Array of ticks (this could be dynamically generated based on min/max)
    ticks = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100];


    // Emit the selected rating when the user changes the slider
    onRatingSelected(event: Event, scale: any) {
        const inputElement = event.target as HTMLInputElement;
        const value = Number(inputElement.value);
        // Handle the value as per the scale index
        console.log(scale.index);
        this.surveyService.setRating(scale.index, value);


        console.log(`Scale: ${scale.name}, Rating: ${value}`);
        // You can integrate this with a service to store the results
    }

    // onScaleClick(value: number) {
    //     console.log(this.scaleIndex)
    //     console.log(value+ "llll")
    //
    //     this.surveyService.setRating(this.scaleIndex, value);
    // }

}
