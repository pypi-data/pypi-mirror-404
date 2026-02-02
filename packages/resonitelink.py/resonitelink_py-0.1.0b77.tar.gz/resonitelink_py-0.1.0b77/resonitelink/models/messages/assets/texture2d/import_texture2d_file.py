from resonitelink.models.messages import Message
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'ImportTexture2DFile',
)


@json_model("importTexture2DFile", Message)
class ImportTexture2DFile(Message):
    """
    Import a texture asset from a file on the local file system. Note that this must be a file
    format supported by Resonite, otherwise this will fail. 
    If you are unsure if the file format is supported, send raw texture data instead.
    
    """
    # Path of the texture file to import.
    file_path : str = json_element("filePath", str, default=MISSING)
