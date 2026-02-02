from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'BoneWeightRawData',
)


@json_model()
class BoneWeightRawData():
    """
    Maps vertex to a specific bone with specific weight.
    
    """
    # Index of the bone this maps too in the Bones list of the mesh.
    bone_index : int = json_element("boneIndex", int, default=MISSING)

    # Weight from 0...1 that influences how much is this vertex affected by the bone.
    weight : float = json_element("weight", float, default=MISSING)
