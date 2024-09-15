import {Injectable} from '@angular/core';
import {HttpRequest, HttpHandler, HttpEvent, HttpInterceptor} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {catchError} from 'rxjs/operators';
import {BackendService, AlertService} from '../service';


@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  constructor(public alertService: AlertService,
              public backendService: BackendService
  ) {
  }

  options = {
    autoClose: true,
    keepAfterRouteChange: false
  };

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(catchError(err => {
      console.log('aqui')
      if (err.status === 400 || err.status === 404|| err.status === 500) {
        console.log(err)
        this.alertService.error(err.error.message, this.options);

        // TODO descomentar isto
        //this.userService.logout();
      }
      console.log(err)

      const error = err.error.message || err.statusText;

      return throwError(error);
    }));
  }
}
