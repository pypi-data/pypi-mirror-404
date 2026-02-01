import os
from http import HTTPStatus
from pathlib import Path

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from pycognito.utils import RequestsSrpAuth, TokenType

from tinesight._api import TinesightApiMixin

# Cognito configuration - these should be set before using TinesightRegistrar
# TODO (NP) figure out how to switch between dev and prod
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "us-east-1_mNTHmkVBB")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "7e77oj9t00qakod07crel9s82t")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


class TinesightRegistrar(TinesightApiMixin):
    """
    Represents a Tinesight tenant, with functionality for generating a signed certificate per device.

    Examples:
        >>> tsr = TinesightRegistrar()
        >>> tsr.login(my_tinesight_account_user_name, my_tinesight_account_password)
        >>> cert = tsr.register_device(my_local_key_path, device_id)
        >>> with open('mydevice.crt', 'w') as fp:
        >>>     fp.write(cert)

    By following this example you can then instantiate a TinesightClient to invoke the Tinesight API.
    """

    def __init__(
        self, country_name: str = "US", state: str | None = None, organization: str | None = None
    ):
        if not COGNITO_USER_POOL_ID or not COGNITO_CLIENT_ID:
            raise ValueError(
                "COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID must be set as environment variables"
            )
        self.auth: RequestsSrpAuth | None = None
        self.country_name = country_name
        self.state = state
        self.organization = organization

    def login(self, username: str, password: str) -> "TinesightRegistrar":
        """
        Basic login to using Cognito IDP with the SRP flow. This method is required to be called
        prior to registering any devices.
        """
        self.auth = RequestsSrpAuth(
            username=username,
            password=password,
            user_pool_id=COGNITO_USER_POOL_ID,
            client_id=COGNITO_CLIENT_ID,
            user_pool_region=AWS_REGION,
            auth_token_type=TokenType.ID_TOKEN,
        )
        return self

    @staticmethod
    def _read_private_key(pem_key_path: Path, key_password: str | None = None):
        # load the private key
        with open(pem_key_path, "rb") as fp:
            pk_contents = fp.read()
        return serialization.load_pem_private_key(
            pk_contents, password=key_password.encode() if key_password else None
        )

    def _is_authorized(self) -> bool:
        if self.auth is None:
            print("Need to call login prior to invoking any API methods")
        return self.auth is not None

    def unregister_device(self, device_id: str):
        """
        Unregisters a device (idempotent) from your account.

        :param device_id: unique device identifier

        :return: dict
        """
        if not self._is_authorized():
            return None
        target_url = self.public_ux_api_uri + "/unregister-device/v1"
        response = requests.post(target_url, json={"device_id": device_id}, auth=self.auth)
        return response.json()

    def register_device(
        self, device_id: str, pem_key_path: Path, key_password: str = None, renew: bool = False
    ) -> bytes | None:
        """
        Registers a uniquely identified device for your account by creating a certificate
        signing request and returning a signed certificate identifying your device, which will
        enable mTLS invocation of the Tinesight API. Certificates expire after one year.

        If a device with this device_id has already been registered and its certificate is not expired,
        an exception will be thrown. If the certificate for this device is expired, a new
        certificate will be returned.

        This method requires the `TinesightRegistrar.login()` method to have been called prior
        to executing.

        :param device_id: unique device identifier
        :param pem_key_path: path to your secret key
        :param key_password: str, default None - password to your secret key
        :param renew: bool, default False - if True, will force a renewal of the certificate

        :return: certificate (bytes)
        """
        if not self._is_authorized():
            return None

        key = self._read_private_key(pem_key_path, key_password)

        # create a certificate signing request
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [
                        # Provide various details about who we are.
                        x509.NameAttribute(NameOID.COUNTRY_NAME, self.country_name),
                        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state or ""),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organization or ""),
                        x509.NameAttribute(NameOID.COMMON_NAME, device_id),
                    ]
                )
            )
            .add_extension(
                x509.ExtendedKeyUsage(
                    [
                        x509.ExtendedKeyUsageOID.CLIENT_AUTH  # Specifies the certificate is for client authentication
                    ]
                ),
                critical=False,
            )
            .add_extension(
                x509.SubjectAlternativeName([x509.RFC822Name(self.auth.username)]), critical=False
            )
            .sign(key, hashes.SHA256())
        )

        # request the signed certificate
        target_url = self.public_ux_api_uri + f"/register-device/v1?renew={int(renew)}"
        response = requests.post(
            target_url,
            data=csr.public_bytes(serialization.Encoding.PEM),
            auth=self.auth,
        )
        if response.status_code == HTTPStatus.OK:
            json_response = response.json()
            return json_response["certificate"].encode("utf-8")
        elif response.status_code == HTTPStatus.CONFLICT:
            json_response = response.json()
            print(json_response["message"])
            return None
        else:
            print("Unable to register device")
            return None
