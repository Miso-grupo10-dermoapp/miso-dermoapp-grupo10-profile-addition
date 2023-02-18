import json
import os

import boto3
from boto3.dynamodb.conditions import Key
import moto
import pytest
from request_validation_utils import body_properties
import app

TABLE_NAME = "dermoapp-patient"


@pytest.fixture
def lambda_environment():
    os.environ[app.ENV_TABLE_NAME] = TABLE_NAME


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def data_table(aws_credentials):
    with moto.mock_dynamodb():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            KeySchema=[
                {"AttributeName": "patient_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "patient_id", "AttributeType": "S"},
            ],
            TableName=TABLE_NAME,
            BillingMode="PAY_PER_REQUEST"
        )

        yield TABLE_NAME


@pytest.fixture
def load_table_speciality(data_table):
    client = boto3.resource("dynamodb")
    table = client.Table(app.ENV_TABLE_NAME)
    result = table.put_item(Item={'doctor_id': '123', 'license_number': '1212',
                                  'status': 'pending',
                                  'specialties': [{'specialty_name': 'dermatologist', 'status': 'pending'}]})
    print(str(result))

@pytest.fixture
def load_table_license(data_table):
    client = boto3.resource("dynamodb")
    table = client.Table(app.ENV_TABLE_NAME)
    result = table.put_item(Item={'doctor_id': '123', 'license_number': '1212',
                                  'status': 'pending'})
    print(str(result))

def test_givenValidInputRequestThenReturn200AndValidPersistence(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/123/profile",
        "httpMethod": "POST",
        "pathParameters": {
            "patient_id": "123"
        },
        "body": "{\n \"photo_type\": \"prof-1\", \"tone_skin\": \"brown\", \"eye_color\": \"blue\",\"hair_coloring\": "
                "\"honey\", \"tan_effect\": \"test\", \"sun_tolerance\": \"low\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    client = boto3.resource("dynamodb", region_name="us-east-1")
    mockTable = client.Table(TABLE_NAME)
    response = mockTable.query(
        KeyConditionExpression=Key('patient_id').eq('123')
    )
    items = response['Items']
    if items:
        data = items[0]

    assert lambdaResponse['statusCode'] == 200
    assert data is not None
    for property in body_properties:
        assert data[property] is not None


def test_givenMissingBodyOnRequestThenReturnError500(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/123/profile",
        "httpMethod": "POST",
        "pathParameters": {
            "patient_id": "123"
        },
        "body": "{}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
    assert '{"message": "cannot proceed with the request error: ' in lambdaResponse['body']


def test_givenMalformedBodyRequestThenReturnError500(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/123/profile",
        "httpMethod": "POST",
        "pathParameters": {
            "patient_id": "123"
        },
        "body": "{\n \"other_field\": \"prof-1\", \"tone_skin\": \"brown\", \"eye_color\": \"blue\",\"hair_coloring\": "
                "\"honey\", \"tan_effect\": \"test\", \"sun_tolerance\": \"low\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
    assert '{"message": "cannot proceed with the request error: Input request is malformed or missing parameters' in lambdaResponse['body']

def test_givenRequestWithoutPatientIDThenReturnError412(lambda_environment, data_table):
    event = {
        "resource": "/patient/{patient_id}/profile",
        "path": "/patient/profile",
        "httpMethod": "POST",
        "pathParameters": {
        },
        "body": "{\n \"other_field\": \"prof-1\", \"tone_skin\": \"brown\", \"eye_color\": \"blue\",\"hair_coloring\": "
                "\"honey\", \"tan_effect\": \"test\", \"sun_tolerance\": \"low\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 412
    assert lambdaResponse['body'] == '{"message": "missing or malformed request body"}'
