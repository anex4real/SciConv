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

    constructor(public router: Router) {
    }

    ngOnInit() {
    }

    public onToggleSidenav = () => {
        this.sidenavToggle.emit();
    };

    goToHome() {
        this.router.navigate(['/']);
    }
}
