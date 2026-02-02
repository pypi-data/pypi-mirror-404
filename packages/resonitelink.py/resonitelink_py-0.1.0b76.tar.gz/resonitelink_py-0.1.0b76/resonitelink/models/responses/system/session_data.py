from resonitelink.models.responses import Response
from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'SessionData',
)


@json_model("sessionData", Response)
class SessionData(Response):
    resonite_version : str = json_element("resoniteVersion", str, default=MISSING)
    resonite_link_version : str = json_element("resoniteLinkVersion", str, default=MISSING)
    unique_session_id : str = json_element("uniqueSessionId", str, default=MISSING)
