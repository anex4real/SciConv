import {NgModule} from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {CommonModule} from '@angular/common';
import {HomeComponent} from "../components/home/home.component";
import {SurveyComponent} from "../components/survey/survey.component";

const routes: Routes = [

        {
            path: '', component: HomeComponent, data: {
                title: 'Home Page'
            }
        },
        {
            path: 'survey/:id', component: SurveyComponent, data: {
                title: 'survey'
            }
        }
];

@NgModule({
    declarations: [],
    imports: [
        CommonModule,
        RouterModule.forRoot(routes)
    ],
    exports: [RouterModule]
})


export class RoutingModule {
}
