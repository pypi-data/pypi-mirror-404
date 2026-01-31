from e80_sdk.internal.environment import Environment, UserApiKey, JobToken
from e80_sdk.internal.httpx_async import async_client
from pydantic import BaseModel


class PlatformClient:
    _env: Environment

    def __init__(self, env: Environment):
        self._env = env

    async def create_sandbox(self) -> "CreateSandboxResponse":
        headers = {}
        if isinstance(self._env.identity, UserApiKey):
            headers["authorization"] = f"Bearer {self._env.identity.api_key}"
        elif isinstance(self._env.identity, JobToken):
            headers["authorization"] = f"Bearer {self._env.identity.job_token}"
            headers["x-8080-job-token"] = "1"

        resp = await async_client.post(
            f"{self._env.base_platform_url}/api/sandbox/{self._env.organization_slug}/{self._env.project_slug}/deploy",
            headers=headers,
        )
        resp.raise_for_status()
        return CreateSandboxResponse.model_validate(resp.json())


class CreateSandboxResponse(BaseModel):
    address: str
    auth_token: str
