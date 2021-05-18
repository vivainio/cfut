from dataclasses import dataclass, replace
from .cli import c


@dataclass
class EcrAddress:
    account: str
    region: str
    repo: str
    tag: str

    def get_path(self):
        return get_ecr_address(self) + f"/{self.repo}:{self.tag}"


def get_ecr_address(ecr: EcrAddress) -> str:
    """ address, region """
    region = ecr.region
    acc = ecr.account
    return f"{acc}.dkr.ecr.{region}.amazonaws.com"


def ecr_login(profile: str, ecr: EcrAddress):
    ecr_address = get_ecr_address(ecr)
    c(f'aws ecr --profile {profile} get-login-password --region {ecr.region} | docker login --password-stdin --username AWS "{ecr_address}"')


def ecr_pull(ecr: EcrAddress):
    c("docker pull " + ecr.get_path())


def ecr_copy(src: EcrAddress, targets: EcrAddress):
    for target in targets:
        t = target.get_path()
        c(f"docker tag {src.get_path()} {t}")
        c("docker push " + t)


src = EcrAddress(
    account="512099555329",
    region="eu-west-1",
    repo="alusta-extract",
    tag="latest"
)

target = replace(src,
                 account="603694106547",
                 repo="test-ecr-repo",
                 tag="release"
                 )


def main():
    #ecr_login("default", src)
    #ecr_pull(src)
    #ecr_login(target)
    ecr_login("q", target)
    ecr_copy(src, [target])



main()
