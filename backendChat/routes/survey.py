# routes/survey.py
import os, json
from datetime import datetime

from flask import Blueprint, request
from flask_cors import cross_origin

import config as cfg
from auth import require_auth
from helpers.index import makeResponse
from flasgger import swag_from


survey_bp = Blueprint("survey", __name__)

@survey_bp.route("/<surveyId>/nasa", methods=['POST'])
@cross_origin()
@require_auth
@swag_from("../swagger/survey/nasa.yml")
def nasa(surveyId):
    requestData = json.loads(request.data)

    number = surveyId + datetime.now(cfg.timezone).strftime("%y%m%d_%H%M")
    file_path = os.path.join(cfg.QUESTIONNAIRES_LOCATION, f"{number}.json")

    with open(file_path, 'w') as json_file:
        json.dump(requestData, json_file, indent=4)

    print(f"Data has been written to {number}.json.")
    return makeResponse([])


