import {MaterialModule} from './material/material.module';
import {AppComponent} from './app.component';
import {TopBarComponent} from './components/top-bar/top-bar.component';
import {SidenavListComponent} from './components/sidenav-list/sidenav-list.component';
import {HeaderComponent} from './components/home/header/header.component';
import {HomeComponent} from './components/home/home.component';
import {FooterComponent} from './components/home/footer/footer.component';
import {BackendService} from "./service";
import {ErrorInterceptor} from "./_helpers/ErrorInterceptor";
import {AlertModule} from "./_alert/alert.module";
import {RoutingModule} from './routing/routing.module';

import {HTTP_INTERCEPTORS, HttpClientModule} from '@angular/common/http';
import {FormsModule} from "@angular/forms";
import {BrowserModule, Title} from '@angular/platform-browser';
import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';
import {NgModule} from "@angular/core";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";


@NgModule({
    imports: [
        BrowserModule,
        MaterialModule,
        HttpClientModule,
        RoutingModule,
        AlertModule,
        FormsModule,
        BrowserAnimationsModule
    ],
    providers: [BackendService, Title,
        {provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true},
    ],
    declarations: [
        AppComponent,
        TopBarComponent,
        SidenavListComponent,
        HeaderComponent,
        HomeComponent,
        FooterComponent,
    ],
    bootstrap: [
        AppComponent
    ]
})
export class AppModule {
}

platformBrowserDynamic().bootstrapModule(AppModule);
