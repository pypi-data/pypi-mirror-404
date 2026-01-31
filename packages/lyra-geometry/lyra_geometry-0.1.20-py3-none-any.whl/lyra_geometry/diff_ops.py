from .tensors import Tensor


def _resolve_space(space, tensor):
    if space is not None:
        return space
    if isinstance(tensor, Tensor):
        return tensor.space
    raise ValueError("Informe space para expressao sem Tensor associado.")


def gradient(tensor, space=None, deriv_position="prepend"):
    space = _resolve_space(space, tensor)
    return space.gradient(tensor, deriv_position=deriv_position)


def divergence(tensor, space=None, position=0, deriv_position="prepend"):
    space = _resolve_space(space, tensor)
    return space.divergence(tensor, position=position, deriv_position=deriv_position)


def laplacian(tensor, space=None, deriv_position="prepend"):
    space = _resolve_space(space, tensor)
    return space.laplacian(tensor, deriv_position=deriv_position)


__all__ = ["divergence", "gradient", "laplacian"]
