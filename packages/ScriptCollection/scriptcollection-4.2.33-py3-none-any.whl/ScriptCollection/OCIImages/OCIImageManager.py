import os
from packaging.version import Version
from ..GeneralUtilities import GeneralUtilities
from ..ScriptCollectionCore import ScriptCollectionCore
from ..ImageUpdater import VersionEcholon
from .AbstractImageHandler import AbstractImageHandler
from .ConcreteImageHandlers.ImageHandlerDebianSlim import ImageHandlerDebianSlim

class OCIImageManager:

    __sc:ScriptCollectionCore=None
    image_handler:list[AbstractImageHandler]

    def __init__(self,sc:ScriptCollectionCore):
        if sc is None:
            sc=ScriptCollectionCore()
        self.__sc=sc
        self.image_handler=[]
        self.image_handler.append(ImageHandlerDebianSlim())

    def get_image_handler(self,image_name:str)->AbstractImageHandler:
        for image_handler in self.image_handler: 
            if image_handler.can_handle(image_name):
                return image_handler
        raise ValueError(f"No image-handler available for image \"{image_name}\".")

    def get_repository_image_definition_file(self,repository:str)->str:
        self.__sc.assert_is_git_repository(repository)
        sc_folder_in_repo=os.path.join(repository,".ScriptCollection")
        GeneralUtilities.ensure_directory_exists(sc_folder_in_repo)
        image_definition_file=os.path.join(sc_folder_in_repo,"ImageDefinition.csv")
        if not os.path.isfile(image_definition_file):
            GeneralUtilities.ensure_file_exists(image_definition_file)
            GeneralUtilities.write_text_to_file(image_definition_file,"ImageName;FallbackRegistryAddress")
        return image_definition_file

    def custom_registry_is_defined(self,image_name:str)->str: 
        docker_image_cache_definition_file=self.__sc.get_global_docker_image_cache_definition_file()
        for line in [f.split(";") for f in GeneralUtilities.read_nonempty_lines_from_file(docker_image_cache_definition_file)[1:]]:
            if image_name==line[0]:
                return True
        return False

    def get_registry_address_for_image(self,repository:str,image_name:str)->str:
        """if image_name==Debian this function returns something like "myregistry.example.com/debian"."""
        if self.custom_registry_is_defined(image_name):
            #return image from custom registry-address
            global_docker_image_cache_definition_file=self.__sc.get_global_docker_image_cache_definition_file()
            for line in [f.split(";") for f in GeneralUtilities.read_nonempty_lines_from_file(global_docker_image_cache_definition_file)[1:]]:
                if image_name==line[0]:
                    return line[1]
        else:
            #return fallback-registry-address
            repository_image_definition_file=self.get_repository_image_definition_file(repository)
            for line in [f.split(";") for f in GeneralUtilities.read_nonempty_lines_from_file(repository_image_definition_file)[1:]]:
                if image_name==line[0]:
                    return line[1]

        raise ValueError(f"No registry defined for image \"{image_name}\".")


    def get_available_versions_of_image_which_are_newer(self,image_name:str,registry_address:str,outdated_version:Version,echolon:VersionEcholon)->list[Version]:
        raise NotImplementedError()#TODO calculate this using get_available_tags_of_image

    def get_available_tags_of_image(self,image_name:str,registry_address:str)->list[str]:
        """registry_address must have one of theese formats: "myregistry.example.com/debian" or "docker.io/debian" or "docker.io/myuser/debian".
        returns something like ["13.2-slim", "13.2", "13.3-slim", "13.3"]."""
        return self.get_image_handler(image_name).get_available_tags_of_image(image_name,registry_address)

    def tag_to_version(self,image_name:str,registry_address:str,tag:str)->Version:
        """registry_address must have one of theese formats: "myregistry.example.com/debian" or "docker.io/debian" or "docker.io/myuser/debian"."""
        return self.get_image_handler(image_name).tag_to_version(image_name,registry_address, tag)

    def version_to_tag(self,image_name:str,registry_address,version:Version)->str:
        """registry_address must have one of theese formats: "myregistry.example.com/debian" or "docker.io/debian" or "docker.io/myuser/debian".
        returns something like "13.3-slim".
        If there are multiple tags available for a certain version then the image-handler decides which one will be returned."""
        return self.get_image_handler(image_name).version_to_tag(image_name,registry_address,version)# 
