#!env python
"""
    I am a sync between hashicorp vault and aws secrets manager.

"""
import argparse
import json
import logging
import os
import subprocess
import sys
import time


import boto3
import hvac


MATCH = os.getenv('AWS_SECRETSMANAGER_PREFIX', 'awssecretsmanager')
VAULT_URL = os.getenv('VAULT_URL', 'http://127.0.0.1:8200')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'secret_token')
LOG_FILE = os.getenv('LOG_FILE', 'file.log')
BACKUP_REGION = os.getenv('BACKUP_REGION', 'us-east-2')
PRIMARY_KMS = os.getenv('PRIMARY_KMS', '')
BACKUP_KMS = os.getenv('BACKUP_KMS', '')


LOG = logging.getLogger(__name__)
LOG_LEVEL = logging.INFO
if os.getenv('DEBUG', None):
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(message)s",
    stream=sys.stdout
)


def _options() -> object:
    """ I provide the argparse option set.

        Returns:
            argparse parser object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('action',
        nargs=1,
        help='What action to take',
        choices=['setup', 'replicate'],
    )
    return parser.parse_args()


def get_secret_id(secret_name: str):
    """
        I return the secret id for a secret_name

        Args:
            secret_name (str): the name of the secret
        Returns:
            str: the aws secret manager id
    """
    client = boto3.client('secretsmanager')
    response = client.list_secrets(
        Filters=[
            {
                'Key': 'name',
                'Values': [secret_name]
            }
        ]
    )
    if response['SecretList']:
        return response['SecretList'][0]['ARN']
    return ''


def replicate_secret(secret_name: str):
    """
        I replicate a secret from vault to secrets manager

        Args:
            secret_name (str): the name of the secret
    """
    vault = hvac.Client(
        url=VAULT_URL,
        token=VAULT_TOKEN,
    )
    secret_value = vault.secrets.kv.read_secret_version(path=secret_name)

    secret_arn = get_secret_id(secret_name)
    client = boto3.client('secretsmanager')
    if secret_arn:
        response = client.update_secret(
            SecretId=secret_arn,
            SecretString=secret_value
        )
    else:
        kwargs = {
            'Name': secret_name,
            'Description': 'vaultsync managed',
            'SecretString': secret_value,
            'AddReplicaRegions': [
                {
                    'Region': BACKUP_REGION,
                }
            ],
            'ForceOverwriteReplicaSecret': True
        }
        if PRIMARY_KMS:
            kwargs['KmsKeyId'] = PRIMARY_KMS
        if BACKUP_KMS:
            kwargs['AddReplicaRegions'][0]['KmsKeyId'] = BACKUP_KMS

        response = client.create_secret(**kwargs)
    LOG.debug(json.dumps(response))


def delete_secret(secret_name: str):
    """
        I replicate a secret from vault to secrets manager

        Args:
            secret_name (str): the name of the secret
    """
    secret_arn = get_secret_id(secret_name)
    if secret_arn:
        client = boto3.client('secretsmanager')
        response = client.delete_secret(
            SecretId=secret_arn,
            ForceDeleteWithoutRecovery=True
        )
        LOG.debug(json.dumps(response))


def tail() -> str:
    """
        generator function that yields in the audit file
    """
    while True:
        try:
            with open(LOG_FILE, 'r', encoding='utf8') as handler:
                file_index = os.stat(LOG_FILE).st_ino
                counter = 0
                while True:
                    line = handler.readline()
                    if not line:
                        time.sleep(0.1)
                        counter += 1
                        if counter > 600:  # 1 minute
                            if file_index != os.stat(LOG_FILE).st_ino:  # file was rotated
                                break
                            counter = 0
                        continue
                    yield line

        # bad try except todo add error handling
        except:  # pylint: disable=bare-except
            pass

def replicate():
    """
        I monitor for secret changes.
    """
    for line in tail():
        try:
            if line.contains(MATCH):
                audit_line = json.loads(line)
                if audit_line['Operation'] in ['create', 'update']:
                    replicate_secret(audit_line['Path'])
                if audit_line['Operation'] in ['delete']:
                    delete_secret(audit_line['Path'])
        # bad try except todo add error handling
        except:  # pylint: disable=bare-except
            pass


def setup():
    """
        I configure vault/secrets manager replicator.
    """
    user = input('What system user should the replication use: ')
    url = input('What vault url to get secrets from: ')
    token = input('What is the token to access vault: ')
    log_file = input('What log file has audit information: ')
    primary_region = input('What primary region for the secret: ')
    primary_kms = input('What is the kms key arn for the primary region: ')
    backup_region = input('What backup region for the secret: ')
    backup_kms = input('What is the kms key arn for the backup region: ')

    with open('/etc/systemd/system/vaultsync.service', 'w', encoding='utf8') as file_handler:
        file_handler.write(f"""
[Unit]
Description=Http Toilet Flusher
Wants=network.target
After=network.target

[Service]
Environment=AWS_SECRETSMANAGER_PREFIX={MATCH}
Environment=VAULT_URL={url}
Environment=VAULT_TOKEN={token}
Environment=LOG_FILE={log_file}
Environment=VAULT_URL={url}
Environment=AWS_DEFAULT_REGION={primary_region}
Environment=BACKUP_REGION={backup_region}
Environment=PRIMARY_KMS={primary_kms}
Environment=BACKUP_KMS={backup_kms}
User={user}

Type=simple
ExecStart={sys.executable} {__file__} replicate

[Install]
WantedBy=multi-user.target
    """)
    subprocess.run(['systemctl', 'daemon-reload'], check=False)
    subprocess.run(['systemctl', 'start', 'vaultsync.service'], check=False)
    subprocess.run(['systemctl', 'enable', 'vaultsync.service'], check=False)


def main():
    """
        The entrypoint to the app
    """
    args = _options()
    if not args.action:
        print('No action provided please specify setup or replicate')
        sys.exit(1)
    globals()[args.action[0]]()


if __name__ == '__main__':
    main()
