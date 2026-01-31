from .core import TensorSpace
from .tensors import Tensor


def _resolve_space_invariant(space, tensor):
    if space is not None:
        return space
    if isinstance(tensor, TensorSpace):
        return tensor
    if isinstance(tensor, Tensor):
        return tensor.space
    raise ValueError("Informe space para calcular invariantes.")


def ricci_scalar(tensor=None, space=None):
    space = _resolve_space_invariant(space, tensor)
    return space.ricci_scalar()


def kretschmann_scalar(tensor=None, space=None):
    space = _resolve_space_invariant(space, tensor)
    return space.kretschmann_scalar()


def euler_density(tensor=None, space=None, normalize=False):
    space = _resolve_space_invariant(space, tensor)
    return space.euler_density(normalize=normalize)


__all__ = ["euler_density", "kretschmann_scalar", "ricci_scalar"]
