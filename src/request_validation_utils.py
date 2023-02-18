import json

body_properties = ["photo_type", "tone_skin", "eye_color", "hair_coloring", "tan_effect", "sun_tolerance"]


def validate_body_params(body):
    try:
        specialties_body = json.loads(body)
        for property in body_properties:
            if not validate_property_exist(property, specialties_body):
                raise RuntimeError("the property {0} is missing or without value".format(property))
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
