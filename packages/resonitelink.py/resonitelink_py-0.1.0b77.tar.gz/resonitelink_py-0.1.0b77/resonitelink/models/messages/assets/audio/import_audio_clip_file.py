from resonitelink.models.messages import Message
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'ImportAudioClipFile',
)


@json_model("importAudioClipFile", Message)
class ImportAudioClipFile(Message):
    """
    Import a audio clip asset from a file on the local file system. Note that this must be a file
    format supported by Resonite, otherwise this will fail. 
    If you are unsure if the file format is supported, send raw audio data instead.
    Generally WAV, OGG & FLAC files are supported as audio clips.
    
    """
    # Path of the audio clip file to import.
    file_path : str = json_element("filePath", str, default=MISSING)
