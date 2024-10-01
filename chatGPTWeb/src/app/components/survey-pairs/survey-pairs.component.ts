import {Component, Input} from '@angular/core';
import {SurveyService} from "../../service/survey.service";

@Component({
  selector: 'app-survey-pairs',
  templateUrl: './survey-pairs.component.html',
  styleUrls: ['./survey-pairs.component.css',  '../../app.component.css']
})
export class SurveyPairsComponent {
  @Input() surveyId: string =''

  constructor(public surveyService: SurveyService) {}

  getCurrentPair() {
    console.log("aqui")
    return this.surveyService.getCurrentPair();
  }


  onSelectChoice(choice: number) {
    console.log("choice"+ choice)
    this.surveyService.tallyResult(choice);
  }
}
