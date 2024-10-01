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

// ,
// {path: 'jupyterhub', component: JupyterComponent},
// {
//   path: 'project/create', component: ProjectComponent, data: {
//     title: 'Project Creation'
//   }
// },
// {
//   path: 'projects', component: ProjectsListComponent, data: {
//     title: 'List Projects'
//   }
// },
// {
//   path: 'project/edit/:id', component: ProjectEditComponent, data: {
//     title: 'Edit the Project'
//   }


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
