import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SurveyPairsComponent } from './survey-pairs.component';

describe('SurveyPairsComponent', () => {
  let component: SurveyPairsComponent;
  let fixture: ComponentFixture<SurveyPairsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SurveyPairsComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SurveyPairsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
