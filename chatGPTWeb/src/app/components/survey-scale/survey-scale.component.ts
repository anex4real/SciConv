import {Component, Input, Output, EventEmitter} from '@angular/core';
import {SurveyService} from "../../service/survey.service";

@Component({
    selector: 'app-survey-scale',
    templateUrl: './survey-scale.component.html',
    styleUrls: ['./survey-scale.component.css', '../../app.component.css']
})
export class SurveyScaleComponent {
    surveyScales: any

    constructor(public surveyService: SurveyService) {
        for (let i = 0; i < 6; i++) {
            //todo alterar
            this.surveyService.setRating(i, null);
            //this.surveyService.setRating(i, 50);
        }
        this.surveyScales = this.surveyService.getScales()

    }



    // Input for the scale name and index
    @Input() scaleName: string = 'Scale';
    @Input() scaleIndex: number = 0;


    // Output event to pass the selected value back to the parent component
    @Output() ratingSelected = new EventEmitter<number>();

    // Current value of the slider
    //todo alterar

    currentValue: number = -1;

    // Array of ticks (this could be dynamically generated based on min/max)
    ticks = [0, 5, 10,15,  20,25,  30,35, 40,45, 50,55, 60,65,  70,75,  80,85, 90,95 ,100];


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
