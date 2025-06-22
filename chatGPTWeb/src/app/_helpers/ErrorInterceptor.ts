import {Injectable} from '@angular/core';
import {HttpRequest, HttpHandler, HttpEvent, HttpInterceptor} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {catchError} from 'rxjs/operators';
import {BackendService, AlertService} from '../service';
import { Router } from '@angular/router';
import { NgZone } from '@angular/core'; // import NgZone



@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(public alertService: AlertService,
              private router: Router,
              private ngZone: NgZone // inject it
  ) {
  }

  options = {
    autoClose: true,
    keepAfterRouteChange: false
  };

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
        catchError(err => {
          console.log('HTTP error intercepted:', err);

          if (err.status !== 200 && err.status !== 201) {
            const message = err.error?.message || 'Unexpected error occurred';
            this.alertService.error(message, this.options);

            // Optional: log out the user or redirect
            // this.userService.logout();
            this.ngZone.run(() => {
              this.router.navigate(['/']);
            });
          }

          const error = err.error?.message || err.statusText || 'Unknown error';
          return throwError(() => error);
        })
    );
  }
}
