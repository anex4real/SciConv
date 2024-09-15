import {Injectable} from '@angular/core';
import {Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot} from '@angular/router';
import {BackendService} from '../service';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(
    private router: Router,
    private backendService: BackendService
  ) {
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
/*    this.backendService.userIsLogged()
      .subscribe(result => {
        console.log(result);
        }
      );*/
    return true;
    // const currentUser = this.userService.currentUserValue;
    // if (currentUser) {
    //   // logged in so return true
    //   return true;
    // }
    //
    // // not logged in so redirect to login page with the return url
    // this.router.navigate(['/login']);
    // return false;
  }
}

