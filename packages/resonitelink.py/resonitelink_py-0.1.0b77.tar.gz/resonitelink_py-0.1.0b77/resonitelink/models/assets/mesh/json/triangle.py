from resonitelink.json import MISSING, json_model, json_element


__all__ = (
    'Triangle',
)


@json_model()
class Triangle():
    """
    Represents a single triangle of a mesh.
    
    """
    # Index of the first vertex that forms this triangle.
    vertex_0_index : int = json_element("vertex0Index", int, default=MISSING)

    # Index of the second vertex that forms this triangle.
    vertex_1_index : int = json_element("vertex1Index", int, default=MISSING)

    # Index of the third vertex that forms this triangle.
    vertex_2_index : int = json_element("vertex2Index", int, default=MISSING)
