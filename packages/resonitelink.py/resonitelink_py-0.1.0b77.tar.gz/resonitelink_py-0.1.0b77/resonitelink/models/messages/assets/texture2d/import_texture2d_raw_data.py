from dataclasses import InitVar, field
from typing import Optional, List
from array import array
from abc import ABC, abstractmethod

from resonitelink.models.messages import Message, BinaryPayloadMessage
from resonitelink.json import MISSING, abstract_json_model, json_model, json_element


__all__ = (
    'ImportTexture2DRawDataBase',
    'ImportTexture2DRawData',
    'ImportTexture2DRawDataHDR',
)


@abstract_json_model()
class ImportTexture2DRawDataBase(BinaryPayloadMessage, ABC):
    _data : Optional[bytes] = field(default=None, init=False)
    
    # Width of the texture.
    width : int = json_element("width", int, default=MISSING)
    
    # Height of the texture.
    height : int = json_element("height", int, default=MISSING)

    @property
    @abstractmethod
    def element_size(self) -> int:
        raise NotImplementedError()

    @property
    def raw_binary_payload(self) -> bytes:
        if not self._data:
            raise RuntimeError("Binary data was never provided!")
        
        return self._data

    @raw_binary_payload.setter
    def raw_binary_payload(self, data : bytes):
        if not self.width:
            raise ValueError("Width cannot be empty!")
        if not self.height:
            raise ValueError("Height cannot be empty!")

        num_elements = self.width * self.height
        len_bytes = num_elements * self.element_size
        if len_bytes != len(data):
            raise ValueError(f"Data size mismatch: Expected: {len_bytes} bytes, Provided: {len(data)} bytes!")

        self._data = data


@json_model("importTexture2DRawData", Message)
class ImportTexture2DRawData(ImportTexture2DRawDataBase):
    # Initializes the image data.
    init_data : InitVar[Optional[List[int]]] = None
    
    # Color profile of the image data.
    color_profile : str = json_element("colorProfile", str, default=MISSING)

    def __post_init__(self, init_data : Optional[List[int]]):
        if init_data:
            self.data = init_data

    @property
    def data(self) -> List[int]:
        arr = array("B")
        arr.frombytes(self.raw_binary_payload)
        return arr.tolist()

    @data.setter
    def data(self, data : List[int]):
        self.raw_binary_payload = array("B", data).tobytes()

    @property
    def element_size(self) -> int:
        return 4 * 1 # color32: 4 * byte


@json_model("importTexture2DRawDataHDR", Message)
class ImportTexture2DRawDataHDR(ImportTexture2DRawDataBase):
    # Initializes the image data.
    init_data : InitVar[Optional[List[float]]] = None

    def __post_init__(self, init_data : Optional[List[float]]):
        if init_data:
            self.data = init_data

    @property
    def data(self) -> List[float]:
        arr = array("f")
        arr.frombytes(self.raw_binary_payload)
        return arr.tolist()

    @data.setter
    def data(self, data : List[float]):
        self.raw_binary_payload = array("f", data).tobytes()

    @property
    def element_size(self) -> int:
        return 4 * 4 # color: 4 * float (4 bytes)
