from packaging.version import Version
from ..AbstractImageHandler import AbstractImageHandler

class ImageHandlerDebian(AbstractImageHandler):

    def can_handle(self,image_name:str)->bool:
        raise NotImplementedError()#TODO

    def get_available_tags_of_image(self,image_name:str,registry_address:str)->list[str]:
        raise NotImplementedError()

    def tag_to_version(self,image_name:str,registry_address:str,tag:str)->Version:
        raise NotImplementedError()
    
    def version_to_tag(self,image_name:str,registry_address:str,version:Version)->str:
        raise NotImplementedError()
