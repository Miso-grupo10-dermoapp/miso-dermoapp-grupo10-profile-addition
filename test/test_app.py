import json
import os

import boto3
from boto3.dynamodb.conditions import Key
import moto
import pytest

import app

TABLE_NAME = "Dermoapp-sprint1-doctor-DoctorDetails-HJ34HOQYTKA6"


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
            AttributeDefinitions=[
                {"AttributeName": "doctor_id", "AttributeType": "S"},
                {"AttributeName": "license_number", "AttributeType": "S"}
            ],
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "doctor_id", "KeyType": "HASH"},
                {"AttributeName": "license_number", "KeyType": "RANGE"}
            ],
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

def test_givenValidInputRequestThenReturn200AndValidPersistence(lambda_environment, load_table_speciality):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/123/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": "{\n    \"specialty_name\": \"dermatologic-verif\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    client = boto3.resource("dynamodb", region_name="us-east-1")
    mockTable = client.Table(TABLE_NAME)
    response = mockTable.query(
        KeyConditionExpression=Key('doctor_id').eq('123')
    )
    items = response['Items']
    if items:
        data = items[0]

    assert lambdaResponse['statusCode'] == 200
    assert data is not None
    assert data['doctor_id'] is not None
    assert data['specialties'] is not None
    assert data['license_number'] is not None
    assert data['doctor_id'] == '123'
    assert data['license_number'] == "1212"
    assert len(data['specialties']) == 2

def test_givenValidInputRequestWithExistingRegistryWithoutSpecialtiesThenReturn200AndValidPersistence(lambda_environment, load_table_license):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/123/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": "{\n    \"specialty_name\": \"dermatologic\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    client = boto3.resource("dynamodb", region_name="us-east-1")
    mockTable = client.Table(TABLE_NAME)
    response = mockTable.query(
        KeyConditionExpression=Key('doctor_id').eq('123')
    )
    items = response['Items']
    if items:
        data = items[0]

    assert lambdaResponse['statusCode'] == 200
    assert data is not None
    assert data['doctor_id'] is not None
    assert data['specialties'] is not None
    assert data['license_number'] is not None
    assert data['doctor_id'] == '123'
    assert data['license_number'] == "1212"
    assert len(data['specialties']) == 1

def test_givenValidInputRequestWithExistingRegistryWithoutSpecialtiesThenReturn200AndValidPersistence(lambda_environment, data_table):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/123/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": "{\n    \"specialty_name\": \"dermatologic-rej\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    client = boto3.resource("dynamodb", region_name="us-east-1")
    mockTable = client.Table(TABLE_NAME)
    response = mockTable.query(
        KeyConditionExpression=Key('doctor_id').eq('123')
    )
    items = response['Items']
    if items:
        data = items[0]

    assert lambdaResponse['statusCode'] == 200
    assert data is not None
    assert data['specialties'] is not None
    assert data['doctor_id'] is not None
    assert data['doctor_id'] == '123'
    assert len(data['specialties']) == 1

def test_givenMissingSpecialtyOnRequestThenReturnError500(lambda_environment, data_table):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/123/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": "{}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
    assert lambdaResponse['body'] == '{"message": "cannot proceed with the request error: Input request is malformed ' \
                                     'or missing parameters, details speciality property cannot be empty"}'


def test_givenMalformedRequestOnRequestThenReturnError412(lambda_environment, data_table):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/license",
        "httpMethod": "POST",
        "pathParameters": {
        },
        "body": "{\n    \"other_field\": \"234353\" \n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 412
    assert lambdaResponse['body'] == '{"message": "missing or malformed request body"}'

def test_givenRequestWithoutBodyThenReturnError412(lambda_environment, data_table):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": None,
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 412
    assert lambdaResponse['body'] == '{"message": "missing or malformed request body"}'


def test_givenValidRequestAndDBFailureThenReturn500(lambda_environment):
    event = {
        "resource": "/doctor/{doctor_id}/license",
        "path": "/doctor/license",
        "httpMethod": "POST",
        "pathParameters": {
            "doctor_id": "123"
        },
        "body": "{\n    \"license_number\": 234353\n}",
        "isBase64Encoded": False
    }
    lambdaResponse = app.handler(event, [])

    assert lambdaResponse['statusCode'] == 500
