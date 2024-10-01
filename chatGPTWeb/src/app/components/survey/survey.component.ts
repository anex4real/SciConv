import {Component} from '@angular/core';
import {SurveyService} from "../../service/survey.service";
import {ActivatedRoute} from "@angular/router";

@Component({
    selector: 'app-survey',
    templateUrl: './survey.component.html',
    styleUrls: ['./survey.component.css', '../../app.component.css']
})
export class SurveyComponent {
    surveyId: string=''

    constructor(public surveyService: SurveyService,
                private route: ActivatedRoute) {
        this.route.params.subscribe(params => {
            this.surveyId = params['id'];
            // @ts-ignore
            if(this.surveyId != "SciConv" && this.surveyId != "codeocean" ) {
                alert('Survey ID:'+  this.surveyId);
            }
            // You can now use this.surveyId to fetch survey data or perform other logic
        });
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
}
