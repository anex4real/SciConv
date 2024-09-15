import {Component, EventEmitter, OnInit, Output} from '@angular/core';
import {Router, ActivatedRoute} from '@angular/router';


@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']

})
export class HeaderComponent implements OnInit {
  @Output() public sidenavToggle = new EventEmitter();
  public username: any;
  options = {
    autoClose: true,
    keepAfterRouteChange: false
  };

  constructor( public router: Router,
  ) {
    // this.userService.getObservableUser().subscribe(user => {
    //   if (user) {
    //     this.username = user.username;
    //   } else {
    //     this.username = null;
    //   }
    // });
  }

  ngOnInit() {
  }

  public onToggleSidenav = () => {
    this.sidenavToggle.emit();
  };

  logout() {
  }

  goToHome() {
    this.router.navigate(['/']);
  }
}
