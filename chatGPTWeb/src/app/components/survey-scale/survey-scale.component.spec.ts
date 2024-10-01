import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SurveyScaleComponent } from './survey-scale.component';

describe('SurveyScaleComponent', () => {
  let component: SurveyScaleComponent;
  let fixture: ComponentFixture<SurveyScaleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SurveyScaleComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SurveyScaleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
