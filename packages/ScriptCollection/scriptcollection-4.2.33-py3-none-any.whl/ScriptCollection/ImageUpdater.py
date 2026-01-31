from abc import abstractmethod, ABC
import json
import re
from urllib.parse import quote
import yaml
import requests
from packaging import version as ve
from packaging.version import Version
from .GeneralUtilities import GeneralUtilities,VersionEcholon
from .ScriptCollectionCore import ScriptCollectionCore


class ImageUpdaterHelper:

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_filter_for_major_and_minor_versions(versions: list[Version], major: int, minor: int) -> Version:
        return [v for v in versions if v.major == major and v.minor == minor]

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_filter_for_major_versions(versions: list[Version], major: int) -> Version:
        return [v for v in versions if v.major == major]

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_and_minor_versions(newer_versions, current_version.major, current_version.minor)
        if len(candidates) == 0:
            return current_version
        result = ImageUpdaterHelper.get_latest_version(candidates)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_or_latest_minor_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major)
        if len(candidates) == 0:
            return current_version
        result = ImageUpdaterHelper.get_latest_version(candidates)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def _internal_get_latest_patch_or_latest_minor_or_next_major_version(newer_versions: list[Version], current_version: Version) -> Version:
        candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major+1)
        if 0 < len(candidates):
            result = ImageUpdaterHelper.get_latest_version(candidates)
            return result
        else:
            candidates = ImageUpdaterHelper._internal_filter_for_major_versions(newer_versions, current_version.major)
            if len(candidates) == 0:
                return current_version
            result = ImageUpdaterHelper.get_latest_version(candidates)
            return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def filter_considering_echolon(newer_versions: list[Version], current_version: Version, version_echolon: VersionEcholon) -> Version:
        if version_echolon == VersionEcholon.LatestPatch:
            return ImageUpdaterHelper._internal_get_latest_patch_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestPatchOrLatestMinor:
            return ImageUpdaterHelper._internal_get_latest_patch_or_latest_minor_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestPatchOrLatestMinorOrNextMajor:
            return ImageUpdaterHelper._internal_get_latest_patch_or_latest_minor_or_next_major_version(newer_versions, current_version)
        elif version_echolon == VersionEcholon.LatestVersion: 
            return ImageUpdaterHelper.get_latest_version(newer_versions)
        else:
            raise ValueError(f"Unknown version-echolon")

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_latest_version(versions: list[Version]) -> Version:
        result = max(versions)
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_latest_version_from_versiontrings(version_strings: list[str]) -> str:
        parsed = [ve.parse(v) for v in version_strings]
        result = max(parsed)
        return str(result)

    @staticmethod
    @GeneralUtilities.check_arguments
    def filter_for_newer_versions(comparison_version: Version, versions_to_filter: list[Version]) -> list[Version]:
        result = [v for v in versions_to_filter if comparison_version < v]
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_versions_in_docker_hub(image: str, search_string: str, filter_regex: str, maximal_amount_of_items_to_load: int = 250) -> list[Version]:#TODO add option to specify image source url
        if "/" not in image:
            image = f"library/{image}"
        response = requests.get(f"https://hub.docker.com/v2/repositories/{quote(image)}/tags?name={quote(search_string)}&ordering=last_updated&page=1&page_size={str(maximal_amount_of_items_to_load)}", timeout=20, headers={'Cache-Control': 'no-cache'})
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data for image {image} from Docker Hub: {response.status_code}")
        response_text = response.text
        data = json.loads(response_text)
        tags: list[str] = [tag["name"] for tag in data["results"] if re.match(filter_regex, tag["name"])]
        versions = [tag.split("-")[0] for tag in tags]
        result = [ve.parse(v) for v in versions]
        return result


class ConcreteImageUpdater(ABC):
    use_fallback_registry_only:bool=False
    _protected_sc:ScriptCollectionCore=None
    
    def __init__(self):
        self._protected_sc=ScriptCollectionCore()

    def custom_registry_for_image_is_defined(self,image:str)->bool:
        return self._protected_sc.custom_registry_for_image_is_defined(image)
    
    @GeneralUtilities.check_arguments
    def get_available_versions_from_custom_registry(self,image:str) -> list[str]:
        """This function assumes that the registry is a custom deployed docker-registry (see https://hub.docker.com/_/registry )"""
        custom_registry_url=self._protected_sc.get_image_with_registry_for_docker_image(image,None,self._protected_sc.default_fallback_docker_registry)
        # registry_base_url= "/".join(custom_registry_url.split("/", 3)[:3]) # with https://
        if custom_registry_url.startswith("https://"):
            registry_base_url=custom_registry_url[8:] # without https://
        else:
            registry_base_url=custom_registry_url
        registry_base_url=registry_base_url.split("/", 1)[0]
        return self._protected_sc.get_tags_of_images_from_registry("https://"+registry_base_url,image,None,None)

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @abstractmethod
    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        raise NotImplementedError


class ConcreteImageUpdaterForNginx(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()

    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["nginx"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Nginx"


class ConcreteImageUpdaterForWordpress(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["wordpress"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Wordpress"


class ConcreteImageUpdaterForGitLab(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}-ce.0"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["gitlab/gitlab-ce", "gitlab/gitlab-ee"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "GitLab"


class ConcreteImageUpdaterForRegistry(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["registry"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Registry"


class ConcreteImageUpdaterForPrometheus(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/prometheus"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Prometheus"


class ConcreteImageUpdaterForPrometheusBlackboxExporter(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/blackbox-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "PrometheusBlackboxExporter"


class ConcreteImageUpdaterForPrometheusNginxExporter(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/nginx-prometheus-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "NginxPrometheusExporter"


class ConcreteImageUpdaterForPrometheusNodeExporter(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["prom/node-exporter"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "PrometheusNodeExporter"


class ConcreteImageUpdaterForKeycloak(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return []  # TODO

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        raise NotImplementedError

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "KeyCloak"


class ConcreteImageUpdaterForMariaDB(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["mariadb"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "MariaDB"


class ConcreteImageUpdaterForPostgreSQL(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["postgres"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag+".0")

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "PostgreSQL"


class ConcreteImageUpdaterForAdminer(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return ["adminer"]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Adminer"


class ConcreteImageUpdaterForDebian(ConcreteImageUpdater):

    def __init__(self):
        super().__init__()

    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\-slim$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}-slim"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self, image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return "debian"

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        GeneralUtilities.assert_condition(tag.endswith("-slim"))
        version_str=tag.split("-")[0]
        if re.match(r"^\d+\.\d+$", version_str):
            version_str=version_str+".0"
        else:
            raise ValueError(f"Cannot parse debian version from tag '{tag}'.")
        return ve.parse(version_str)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return "Debian"


class ConcreteImageUpdaterForGeneric(ConcreteImageUpdater):

    __tool_name:str
    __image_name:str
    def __init__(self,tool_name:str,image_name:str):
        self.__tool_name=tool_name
        self.__image_name=image_name
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return  ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return [self.__image_name]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag)

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return self.__tool_name


class ConcreteImageUpdaterForGenericV(ConcreteImageUpdater):

    __tool_name:str
    __image_name:str
    def __init__(self,tool_name:str,image_name:str):
        self.__tool_name=tool_name
        super().__init__()
    
    @GeneralUtilities.check_arguments
    def get_all_available_versions(self,image:str) -> list[str]:
        if self.custom_registry_for_image_is_defined(image) and not self.use_fallback_registry_only:
            return self.get_available_versions_from_custom_registry(image)
        return ImageUpdaterHelper.get_versions_in_docker_hub(image, ".", "^v\\d+\\.\\d+\\.\\d+$", 999)

    @GeneralUtilities.check_arguments
    def version_to_tag(self,  version: Version) -> str:
        return f"v{version.major}.{version.minor}.{version.micro}"

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self,  image: str, version_echolon: VersionEcholon, current_version: Version) -> Version:
        versions =[Version(v) for v in  self.get_all_available_versions(image)]
        newer_versions = ImageUpdaterHelper.filter_for_newer_versions(current_version, versions)
        result = ImageUpdaterHelper.filter_considering_echolon(newer_versions, current_version, version_echolon)
        return result

    @GeneralUtilities.check_arguments
    def get_supported_images(self) -> list[str]:
        return [self.__image_name]

    @GeneralUtilities.check_arguments
    def get_version_from_tag(self, image: str, tag: str) -> Version:
        return ve.parse(tag[1:])

    @GeneralUtilities.check_arguments
    def get_name(self) -> str:
        return self.__tool_name



class ImageUpdater:

    updater: list[ConcreteImageUpdater] = None

    def __init__(self):
        self.updater = list[ConcreteImageUpdater]()

    def add_default_mapper(self) -> None:
        self.updater.append(ConcreteImageUpdaterForNginx())
        self.updater.append(ConcreteImageUpdaterForWordpress())
        self.updater.append(ConcreteImageUpdaterForGitLab())
        self.updater.append(ConcreteImageUpdaterForRegistry())
        self.updater.append(ConcreteImageUpdaterForPrometheus())
        self.updater.append(ConcreteImageUpdaterForPrometheusBlackboxExporter())
        self.updater.append(ConcreteImageUpdaterForPrometheusNginxExporter())
        self.updater.append(ConcreteImageUpdaterForPrometheusNodeExporter())
        self.updater.append(ConcreteImageUpdaterForKeycloak())
        self.updater.append(ConcreteImageUpdaterForMariaDB())
        self.updater.append(ConcreteImageUpdaterForPostgreSQL())
        self.updater.append(ConcreteImageUpdaterForAdminer())

    @GeneralUtilities.check_arguments
    def check_service_for_newest_version(self, dockercompose_file: str, service_name: str) -> bool:
        imagename, existing_tag, existing_version,original_image = self.get_current_version_of_service_from_docker_compose_file(dockercompose_file, service_name)  # pylint:disable=unused-variable
        newest_version, newest_tag = self.get_latest_version_of_image(imagename, VersionEcholon.LatestVersion, existing_version)  # pylint:disable=unused-variable
        if existing_version < newest_version:
            GeneralUtilities.write_message_to_stdout(f"Service {service_name} with image {imagename} uses tag {existing_version}. The newest available version of this image is {newest_version}.")
            return True
        else:
            return False

    @GeneralUtilities.check_arguments
    def check_for_newest_version(self, dockercompose_file: str, excluded_services: list[str] = []) -> bool:
        all_services = self.get_services_from_docker_compose_file(dockercompose_file)
        services_to_check = [service for service in all_services if service not in all_services]
        newer_version_available: bool = False
        for service_to_check in services_to_check:
            if self.check_service_for_newest_version(dockercompose_file, service_to_check):
                newer_version_available = True
        return newer_version_available

    @GeneralUtilities.check_arguments
    def update_all_services_in_docker_compose_file(self, dockercompose_file: str, version_echolon: VersionEcholon, except_services: list[str] = [], updatertype: str = None):
        all_services = self.get_services_from_docker_compose_file(dockercompose_file)
        services_to_update = [service for service in all_services if service not in except_services]
        self.update_services_in_docker_compose_file(dockercompose_file, services_to_update, version_echolon, updatertype)

    @GeneralUtilities.check_arguments
    def update_services_in_docker_compose_file(self, dockercompose_file: str, service_names: list[str], version_echolon: VersionEcholon, updatertype: str = None):
        for service_name in service_names:
            if self.service_has_image_information(dockercompose_file, service_name):
                self.update_service_in_docker_compose_file(dockercompose_file, service_name, version_echolon, updatertype)

    @GeneralUtilities.check_arguments
    def service_has_image_information(self, dockercompose_file: str, service_name: str) -> bool:
        with open(dockercompose_file, 'r', encoding="utf-8") as file:
            compose_data = yaml.safe_load(file)
            service = compose_data.get('services', {}).get(service_name, {})
            image = service.get('image', None)
            return image is not None

    @GeneralUtilities.check_arguments
    def update_service_in_docker_compose_file(self, dockercompose_file: str, service_name: str, version_echolon: VersionEcholon, updatertype: str = None):
        imagename, existing_tag, existing_version,original_image = self.get_current_version_of_service_from_docker_compose_file(dockercompose_file, service_name)  # pylint:disable=unused-variable
        result = self.get_latest_version_of_image(imagename, version_echolon, existing_version, updatertype)
        newest_version = result[0]
        newest_tag = result[1]
        # TODO write info to console if there is a newwer version available if versionecoholon==latest would have been chosen
        sc=ScriptCollectionCore()
        if existing_version < newest_version:

            with open(dockercompose_file, 'r', encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})
            if service_name not in services:
                raise ValueError(f"Service '{service_name}' not found.")

            image = services[service_name].get("image")
            if not image:
                raise ValueError(f"Service '{service_name}' does not have an image-field.")
            match = re.search(r"\$\{([^}]+)\}", image)
            if match:
                variable=match.group(1)
                if variable.startswith("image_"):
                    image_name:str=variable.split("_")[1]
                    tag=image.split(":")[1]
                    image=sc.get_image_with_registry_for_docker_image(image_name,None,sc.default_fallback_docker_registry)+":"+tag

            imagename = image.split(":")[0]
            services[service_name]["image"] = original_image+":"+newest_tag

            with open(dockercompose_file, 'w', encoding="utf-8") as f:
                yaml.dump(compose_data, f, default_flow_style=False)

    

    @GeneralUtilities.check_arguments
    def __resolve_variable(self, image: str) -> str:
        sc=ScriptCollectionCore()
        match = re.search(r"\$\{([^}]+)\}", image)
        if match:
            variable=match.group(1)
            if variable.startswith("image_"):
                image_name:str=variable.split("_")[1]
                tag=image.split(":")[1]
                image=sc.get_image_with_registry_for_docker_image(image_name,None,sc.default_fallback_docker_registry)+":"+tag
        return image

    @GeneralUtilities.check_arguments
    def get_current_version_of_service_from_docker_compose_file(self, dockercompose_file: str, service_name: str) -> tuple[str, str, Version,str]:
        """returns (image,existing_tag,existing_version,original_image)"""
        with open(dockercompose_file, 'r', encoding="utf-8") as file:
            compose_data = yaml.safe_load(file)
            service = compose_data.get('services', {}).get(service_name, {})
            original_image = str(service.get('image', None))
            image=self.__resolve_variable(original_image)
            if image:
                if ':' in image:
                    name, tag = image.rsplit(':', 1)
                else:
                    name, tag = image, 'latest'
                return name, tag, self.get_docker_version_from_tag(name, tag), original_image
            else:
                raise ValueError(f"Service '{service_name}' in '{dockercompose_file}'")

    @GeneralUtilities.check_arguments
    def get_updater_for_image(self,  image: str) -> ConcreteImageUpdater:
        if "/" in image:
            image=image.rsplit("/", 1)[-1]
        for updater in self.updater:
            for supported_image_regex in updater.get_supported_images():
                r = re.compile("^"+supported_image_regex+"$")
                if r.match(image):
                    return updater
        raise ValueError(f"No updater available for image '{image}'")

    @GeneralUtilities.check_arguments
    def __get_updater_by_name(self,  updater_name: str) -> ConcreteImageUpdater:
        for updater in self.updater:
            if updater.get_name() == updater_name:
                return updater
        raise ValueError(f"No updater available with name '{updater_name}'")

    @GeneralUtilities.check_arguments
    def get_docker_version_from_tag(self,  image: str, tag: str) -> Version:
        updater: ConcreteImageUpdater = self.get_updater_for_image(image)
        return updater.get_version_from_tag(image, tag)

    @GeneralUtilities.check_arguments
    def get_latest_version_of_image(self, image: str, version_echolon: VersionEcholon, current_version: Version, updatertype: str = None) -> tuple[Version, str]:

        updater: ConcreteImageUpdater = None
        if updatertype is None:
            updater=self.get_updater_for_image(image)
        else:
            updater=self.__get_updater_by_name(updatertype)

        newest_version: Version = updater.get_latest_version_of_image(image, version_echolon, current_version)
        newest_tag: str = updater.version_to_tag(newest_version)
        return (newest_version, newest_tag)

    @GeneralUtilities.check_arguments
    def get_services_from_docker_compose_file(self, dockercompose_file: str) -> list[str]:
        with open(dockercompose_file, 'r', encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)
            services = compose_data.get('services', {})
            result = list(services.keys())
            return result
