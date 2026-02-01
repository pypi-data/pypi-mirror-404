import json
import os

from kumoai.experimental.rfm.backend.snow import Connection
from kumoai.experimental.rfm.backend.snow import connect as _connect


def connect(
    region: str,
    id: str,
    account: str,
    user: str,
    warehouse: str | None = None,
    database: str | None = None,
    schema: str | None = None,
) -> Connection:

    kwargs = dict(password=os.getenv('SNOWFLAKE_PASSWORD'))
    if kwargs['password'] is None:
        import boto3
        from cryptography.hazmat.primitives import serialization

        client = boto3.client(
            service_name='secretsmanager',
            region_name=region,
        )
        secret_id = (f'arn:aws:secretsmanager:{region}:{id}:secret:'
                     f'{account}.snowflakecomputing.com')
        response = client.get_secret_value(SecretId=secret_id)['SecretString']
        secret = json.loads(response)

        private_key = serialization.load_pem_private_key(
            secret['kumo_user_secretkey'].encode(),
            password=None,
        )
        kwargs['private_key'] = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    return _connect(
        account=account,
        user=user,
        warehouse=warehouse or 'WH_XS',
        database=database or 'KUMO',
        schema=schema,
        session_parameters=dict(CLIENT_TELEMETRY_ENABLED=False),
        **kwargs,
    )
