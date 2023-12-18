from keras.src import backend
from keras.src.mixed_precision.dtype_policy import DTypePolicy
from keras.src.mixed_precision.dtype_policy import dtype_policy
from keras.src.mixed_precision.dtype_policy import set_dtype_policy
from keras.src.saving import serialization_lib


def resolve_policy(identifier):
    if identifier is None:
        return dtype_policy()
    if isinstance(identifier, DTypePolicy):
        return identifier
    if isinstance(identifier, dict):
        return serialization_lib.deserialize_keras_object(identifier)
    if isinstance(identifier, str):
        return DTypePolicy(identifier)
    try:
        return DTypePolicy(backend.standardize_dtype(identifier))
    except:
        raise ValueError(
            "Cannot interpret `dtype` argument. Expected a string "
            f"or an instance of DTypePolicy. Received: dtype={identifier}"
        )

