import { Component } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { Title } from '@angular/platform-browser';
import { filter, map } from 'rxjs/operators';
import {BackendService} from "./service";


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  preserveWhitespaces: true,

})
export class AppComponent {

  constructor(private router: Router, private activatedRoute: ActivatedRoute, private titleService: Title, protected backend: BackendService) {

    this.backend.getServerHome().subscribe((response: any) => {
      console.log(response)
      console.log("successful server connection")
    })

    this.router.events.pipe(
      filter((event: any) => event instanceof NavigationEnd),
      map(() => {
        let child = this.activatedRoute.firstChild;
        while (child) {
          if (child.firstChild) {
            child = child.firstChild;
          } else if (child.snapshot.data && child.snapshot.data['title']) {
            return child.snapshot.data['title'];
          } else {
            return null;
          }
        }
        return null;
      })
    ).subscribe((data: any) => {
      if (data) {
        this.titleService.setTitle(data);
      }
    });
  }
}
