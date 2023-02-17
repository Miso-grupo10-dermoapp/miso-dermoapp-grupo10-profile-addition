import json

from db_service import insert_item, get_item
from request_validation_utils import validate_body_specialty, validate_property_exist, specialty_property_name
from request_response_utils import return_error_response, return_status_ok

ENV_TABLE_NAME = "Dermoapp-sprint1-doctor-DoctorDetails-HJ34HOQYTKA6"


def handler(event, context):
    try:
        print("lambda execution with context {0}".format(str(context)))
        if validate_property_exist("doctor_id", event['pathParameters']) and validate_property_exist('body', event):
            if validate_body_specialty(event['body']):
                doctor_id = event['pathParameters']['doctor_id']
                response = add_doctor_speciality(event, doctor_id)
                return return_status_ok(response)
        else:
            return return_error_response("missing or malformed request body", 412)
    except Exception as err:
        return return_error_response("cannot proceed with the request error: " + str(err), 500)

def add_doctor_speciality(request, doctor_id):
    parsed_body = json.loads(request["body"])
    persisted_data = get_item("doctor_id", doctor_id)
    speciality_json = {
        specialty_property_name: parsed_body[specialty_property_name],
        'status': get_status_from_input(parsed_body[specialty_property_name])
    }
    if persisted_data or persisted_data != []:
        if 'specialties' in persisted_data:
            persisted_data['specialties'].append(speciality_json)
        else:
            persisted_data['specialties'] = [speciality_json]
        insert_item(persisted_data)
        return get_item("doctor_id", doctor_id)
    else:
        registry = { 'doctor_id': doctor_id, 'license_number': 'no_applies', 'specialties': [speciality_json]}
        insert_item(registry)
        return get_item("doctor_id", doctor_id)


def get_status_from_input(speciality):
    if "-verif" in speciality:
        return "Verified"
    if "-rej" in speciality:
        return "Rejected"
    return "Pending"
