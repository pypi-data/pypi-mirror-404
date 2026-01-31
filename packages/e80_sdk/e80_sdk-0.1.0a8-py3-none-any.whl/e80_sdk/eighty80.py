import os
import openai

from typing import AsyncIterator, overload, Optional
from contextlib import asynccontextmanager
from e80_sdk.internal.platform import PlatformClient
from e80_sdk.errors import Eighty80FatalError
from e80_sdk.secrets import Secrets
from e80_sdk.sandbox import SandboxClient
from e80_sdk.internal.environment import Environment, UserApiKey, JobToken
from openai.resources.responses.responses import Responses, AsyncResponses
from openai.resources.chat.chat import Chat, AsyncChat
from openai.resources.models import Models, AsyncModels
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Instrument all HTTPX clients with OpenTelemetry
# Since we do not manually pass in clients into OpenAI SDK,
# we simply do this to get the calls to OpenAI instrumented.
HTTPXClientInstrumentor().instrument()


class Eighty80:
    """
    The main entrypoint into the 8080 SDK.

    Call its methods to access different 8080 services.
    """

    _cached: tuple[Secrets, Environment] | None = None
    _environment: Environment
    _secrets: Secrets

    def __init__(
        self, *, env: Optional[Environment] = None, secrets: Optional[Secrets] = None
    ):
        if env is not None and secrets is not None:
            self._environment = env
            self._secrets = secrets
        # Use a cached version of the environment and secrets if called with
        # no arguments.
        elif Eighty80._cached:
            self._secrets, self._environment = Eighty80._cached
        else:
            load = self._load_environment()
            Eighty80._cached = load
            self._secrets, self._environment = load

    def secrets(self) -> Secrets:
        return self._secrets

    @overload
    def completion_sdk(self) -> "_Eighty80OpenAISDK": ...

    @overload
    def completion_sdk(self, secret_name: str) -> openai.OpenAI: ...

    def completion_sdk(self, secret_name: str | None = None):
        """
        Obtain an OpenAI SDK-compatible object that can be a drop-in
        replacement for the OpenAI SDK client.

        ```python
        from openai import OpenAI
        from e80_sdk import Eighty80

        old_client = OpenAI(...)
        drop_me_in = Eighty80.completion_sdk(...)
        ```

        To use 8080 models, simply call this method without any arguments.
        Note that not all properties are implemented for 8080 models.

        ```python
        from e80_sdk import Eighty80

        Eighty80.completion_sdk().responses.create(...)
        Eighty80.completion_sdk().chat.completions.create(...)
        ```

        You can set an OpenAI SDK secret in the 8080 platform, and obtain
        an OpenAI SDK-compatible object. An SDK object created this way has
        no restrictions on what properties are available.

        ```python
        from e80_sdk import Eighty80

        # Assumes 'foo' is an OpenAI SDK secret set in the 8080 platform
        Eighty80.completion_sdk('foo').chat.completions.create(...)
        ```
        """
        if secret_name is None:
            return _Eighty80OpenAISDK(self._environment)

        secret = self.secrets().get_openai_secret(secret_name)
        return openai.OpenAI(base_url=secret.url, api_key=secret.api_key)

    @overload
    def async_completion_sdk(self) -> "_Eighty80OpenAIAsyncSDK": ...

    @overload
    def async_completion_sdk(self, secret_name: str) -> openai.AsyncOpenAI: ...

    def async_completion_sdk(self, secret_name: str | None = None):
        """
        Obtain an async OpenAI SDK-compatible object that can be a drop-in
        replacement for the async OpenAI SDK client.

        ```python
        from openai import AsyncOpenAI
        from e80_sdk import Eighty80

        old_client = AsyncOpenAI(...)
        drop_me_in = Eighty80.async_completion_sdk(...)
        ```

        To use 8080 models, simply call this method without any arguments.
        Note that not all properties are implemented for 8080 models.

        ```python
        from e80_sdk import Eighty80

        await Eighty80.async_completion_sdk().responses.create(...)
        await Eighty80.async_completion_sdk().chat.completions.create(...)
        ```

        You can set an OpenAI SDK secret in the 8080 platform, and obtain
        an async OpenAI SDK-compatible object. An SDK object created this way has
        no restrictions on what properties are available.

        ```python
        from e80_sdk import Eighty80

        # Assumes 'foo' is an OpenAI SDK secret set in the 8080 platform
        await Eighty80.async_completion_sdk('foo').chat.completions.create(...)
        ```
        """

        if secret_name is None:
            return _Eighty80OpenAIAsyncSDK(self._environment)

        secret = self.secrets().get_openai_secret(secret_name)
        return openai.AsyncOpenAI(base_url=secret.url, api_key=secret.api_key)

    @asynccontextmanager
    async def sandbox(self) -> AsyncIterator[SandboxClient]:
        """
        Create a new sandbox where you can execute arbitrary Python
        and Javascript code.

        Use this as an async context manager so the sandbox will get cleaned up
        automatically.

        ```
        from e80_sdk import Eighty80

        async with Eighty80.sandbox() as sandbox_client:
            sandbox_client.run_python("print('hello world')")
            sandbox_client.install_python_dependencies(["requests"])
        ```
        """
        client = PlatformClient(self._environment)

        sb_resp = await client.create_sandbox()
        sb_client = SandboxClient(sb_resp.auth_token, sb_resp.address)
        sb_client.wait_until_ready()

        try:
            yield sb_client
        finally:
            sb_client.destroy()

    def _load_environment(self) -> tuple[Secrets, Environment]:
        """
        Loads the 8080 environment from environment variables and Nomad files.

        Basically, this is used for loading jobs running in prod.

        Note, the environment can be populated manually via the constructor.
        More options are available when creating the environment manually.
        """

        # Required env variables - MUST be populated no matter what.
        project_slug = os.environ["8080_PROJECT_SLUG"]
        org_slug = os.environ["8080_ORGANIZATION_SLUG"]

        # Optional env variables
        api_url = os.environ.get("8080_API_URL", "https://api.8080.io")
        platform_url = os.environ.get("8080_PLATFORM_URL", "https://app.8080.io")
        use_secrets_file = os.environ.get("8080_SECRETS_FILE", None)
        secrets_json = os.environ.get("8080_SECRETS_JSON", None)

        # One of these MUST be set.
        identity_token = os.environ.get("8080_IDENTITY_TOKEN", None)
        user_api_key = os.environ.get("8080_API_KEY", None)

        identity: JobToken | UserApiKey | None = None
        if identity_token:
            identity = JobToken(job_token=identity_token)
        elif user_api_key:
            identity = UserApiKey(api_key=user_api_key)
        if identity is None:
            raise Eighty80FatalError(
                "Identity was None. Did you populate 8080_IDENTITY_TOKEN or 8080_API_KEY?"
            )

        return Secrets(
            secrets_file="/local/secrets.json" if use_secrets_file else None,
            secrets_json=secrets_json,
        ), Environment(
            organization_slug=org_slug,
            project_slug=project_slug,
            identity=identity,
            base_platform_url=platform_url,
            base_api_url=api_url,
        )


class _Eighty80OpenAISDK:
    _cached_client: openai.OpenAI

    def __init__(self, env: Environment):
        client = None

        if isinstance(env.identity, JobToken):
            client = openai.OpenAI(
                api_key=env.identity.job_token,
                base_url=f"{env.base_api_url}/v1",
                default_headers={"x-8080-job-token": "1"},
            )
        elif isinstance(env.identity, UserApiKey):
            client = openai.OpenAI(
                api_key=env.identity.api_key,
                base_url=f"{env.base_api_url}/v1",
                default_headers={"x-8080-project-slug": env.project_slug},
            )
        if client is None:
            raise Exception("Somehow got a null client")
        self._cached_client = client

    @property
    def chat(self) -> Chat:
        return self._cached_client.chat

    @property
    def models(self) -> Models:
        return self._cached_client.models

    @property
    def responses(self) -> Responses:
        return self._cached_client.responses


class _Eighty80OpenAIAsyncSDK:
    _cached_client: openai.AsyncOpenAI

    def __init__(self, env: Environment):
        client = None
        if isinstance(env.identity, JobToken):
            client = openai.AsyncOpenAI(
                api_key=env.identity.job_token,
                base_url=f"{env.base_api_url}/v1",
                default_headers={"x-8080-job-token": "1"},
            )
        elif isinstance(env.identity, UserApiKey):
            client = openai.AsyncOpenAI(
                api_key=env.identity.api_key,
                base_url=f"{env.base_api_url}/v1",
                default_headers={"x-8080-project-slug": env.project_slug},
            )
        if client is None:
            raise Exception("Somehow got a null client")
        self._cached_client = client

    @property
    def chat(self) -> AsyncChat:
        return self._cached_client.chat

    @property
    def models(self) -> AsyncModels:
        return self._cached_client.models

    @property
    def responses(self) -> AsyncResponses:
        return self._cached_client.responses
