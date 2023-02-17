import json

specialty_property_name = "specialty_name"


def validate_body_specialty(body):
    try:
        specialties_body = json.loads(body)
        if not validate_property_exist(specialty_property_name, specialties_body):
            raise RuntimeError("speciality property cannot be empty")
    except Exception as err:
        raise RuntimeError("Input request is malformed or missing parameters, details " + str(err))
    return True


def validate_property_exist(property, loaded_body):
    if property in loaded_body:
        if loaded_body[property] is not None:
            return True
        else:
            return False
    else:
        return False
