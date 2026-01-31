from dataclasses import dataclass


@dataclass
class UserApiKey:
    api_key: str


@dataclass
class JobToken:
    job_token: str


@dataclass
class Environment:
    organization_slug: str
    project_slug: str
    identity: UserApiKey | JobToken
    base_platform_url: str
    base_api_url: str
