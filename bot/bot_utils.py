import paramiko
from dotenv import load_dotenv
import os


load_dotenv()

KEY_PATH = os.getenv('SSH_PRIVATE_KEY_PATH')
HOST = os.getenv('VPS_IP')
USERNAME = os.getenv('VPS_USERNAME')


def upload_file_to_vps(
    local_file: str,
    remote_file: str,
    host: str = HOST,
    username: str = USERNAME,
    key_path: str = KEY_PATH,
    port: int = 22
):

    transport = paramiko.Transport((host, port))

    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path)

        transport.connect(
            username=username,
            pkey=key
        )

        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.put(
            local_file,
            remote_file
        )

        sftp.close()

    finally:
        transport.close()


if __name__ == '__main__':
    upload_file_to_vps(
        'bot/images/for_tg/2026-06-22_14-06-10.749_972.jpg',
        '/root/wdstats/bot/images/for_tg/2026-06-22_14-06-10.749_9723.jpg',
        HOST,
        USERNAME,
        KEY_PATH
    )