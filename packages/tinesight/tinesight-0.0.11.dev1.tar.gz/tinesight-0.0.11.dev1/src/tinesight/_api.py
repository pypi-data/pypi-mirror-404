import os


class TinesightApiMixin:

    @property
    def tenant_base_api_uri(self) -> str:
        subdomain = "devapi" if os.getenv("TINESIGHT_DEV") else "api"
        return f"https://{subdomain}.tinesight.com"

    @property
    def public_ux_api_uri(self) -> str:
        api_ref = "17bx575oxl" if os.getenv("TINESIGHT_DEV") else "api"
        return f"https://{api_ref}.execute-api.us-east-1.amazonaws.com"
