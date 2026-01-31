import itertools
import numbers
import sympy as sp


class Index:
    def __init__(self, name):
        self.name = str(name)

    def __repr__(self):
        return self.name

    def __pos__(self):
        return UpIndex(self.name)

    def __neg__(self):
        return DownIndex(self.name)


class _NoLabel:
    pass


NO_LABEL = _NoLabel()


class UpIndex:
    def __init__(self, label=NO_LABEL):
        self.label = label

    def __repr__(self):
        return f"^{self.label}"


class DownIndex:
    def __init__(self, label=NO_LABEL):
        self.label = label

    def __repr__(self):
        return f"_{self.label}"


class CoordIndex(Index):
    def __init__(self, name, coord_pos):
        super().__init__(name)
        self.coord_pos = coord_pos


class Up:
    def __call__(self, label=NO_LABEL):
        return UpIndex(label)


class Down:
    def __call__(self, label=NO_LABEL):
        return DownIndex(label)


U = Up()

D = Down()

u = U

d = D


def _norm_sig(sig, rank):
    if len(sig) != rank:
        raise ValueError(f"Signature has length {len(sig)} but rank is {rank}.")
    out = []
    for s in sig:
        if s in (U, Up, "U", "u", "^", +1, True):
            out.append(U)
        elif s in (D, Down, "D", "d", "_", -1, False):
            out.append(D)
        else:
            raise ValueError(f"Invalid signature element: {s!r}. Use U/D.")
    return tuple(out)


def _validate_signature(signature, rank):
    if not isinstance(signature, (tuple, list)):
        raise TypeError("signature must be a tuple/list, e.g. (U, D, D).")
    if len(signature) != rank:
        raise ValueError(f"signature has length {len(signature)}, but rank={rank}.")
    return _norm_sig(signature, rank)


def table(func, dim, rank):
    shape = (dim,) * rank
    flat = [func(*idx) for idx in itertools.product(range(dim), repeat=rank)]
    return sp.ImmutableDenseNDimArray(flat, shape)


class Tensor:
    def __init__(self, components, space, signature, name=None, label=None):
        self.components = sp.Array(components)
        self.rank = self.components.rank()
        self.signature = _validate_signature(signature, self.rank)
        self.space = space
        self.name = name if name is not None else space._next_tensor_name()
        self.label = label if label is not None else self.name
        self._cache = {self.signature: self.components}

    def _as_scalar(self):
        if self.rank != 0:
            raise TypeError("Scalar operation is only valid for rank-0 tensors.")
        return sp.sympify(self.components[()])

    def fmt(self, expr=None):
        if expr is None:
            if self.rank == 0:
                target = sp.expand(sp.simplify(self._as_scalar()))
                return Tensor(sp.Array(target), self.space, signature=self.signature, name=self.name, label=self.label)
            if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
                arr = sp.ImmutableDenseNDimArray(self.components)
                target = arr.applyfunc(lambda v: sp.expand(sp.simplify(v)))
            else:
                target = sp.expand(sp.simplify(self.components))
            return Tensor(target, self.space, signature=self.signature, name=self.name, label=self.label)
        if isinstance(expr, Tensor):
            return expr.fmt()
        if isinstance(expr, IndexedTensor):
            return expr.fmt()
        return sp.expand(sp.simplify(expr))

    def subs(self, *args, **kwargs):
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [v.subs(*args, **kwargs) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = self.components.subs(*args, **kwargs)
        return Tensor(target, self.space, signature=self.signature, name=self.name, label=self.label)

    @property
    def expr(self):
        return self._as_scalar()

    @property
    def args(self):
        return self._as_scalar().args

    def _sympy_(self):
        if self.rank != 0:
            raise sp.SympifyError(self)
        return self._as_scalar()

    def _repr_latex_(self):
        if self.rank == 0:
            expr = self._as_scalar()
            if hasattr(expr, "_repr_latex_"):
                return expr._repr_latex_()
            return sp.latex(expr)
        if hasattr(self.components, "_repr_latex_"):
            return self.components._repr_latex_()
        return sp.latex(self.components)

    def __call__(self, *sig):
        if len(sig) == 1 and isinstance(sig[0], (tuple, list)):
            sig = tuple(sig[0])
        if sig and any(isinstance(s, Index) for s in sig):
            raise TypeError("Use +a/-b for indices with explicit variance.")
        if sig and all(isinstance(s, (UpIndex, DownIndex)) for s in sig):
            if len(sig) != self.rank:
                raise ValueError("Number of indices does not match tensor rank.")
            up = [None] * self.rank
            down = [None] * self.rank
            for i, idx in enumerate(sig):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                else:
                    down[i] = idx.label
            return self.idx(up=up, down=down)
        arr = self.as_signature(sig, simplify=False)
        return Tensor(arr, self.space, signature=sig, name=self.name, label=self.label)

    def __getitem__(self, indices):
        if not isinstance(indices, tuple):
            indices = (indices,)
        if any(isinstance(idx, (UpIndex, DownIndex, Index)) for idx in indices):
            if any(isinstance(idx, Index) for idx in indices):
                raise TypeError("Use +a/-b for indices with explicit variance.")
            if not all(isinstance(idx, (UpIndex, DownIndex)) for idx in indices):
                raise TypeError("Use only +a/-b (or U(a)/D(b)) to index the tensor.")
            if len(indices) != self.rank:
                raise ValueError("Number of indices does not match tensor rank.")
            up = [None] * self.rank
            down = [None] * self.rank
            for i, idx in enumerate(indices):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                elif isinstance(idx, DownIndex):
                    down[i] = idx.label
            indexed = self.idx(up=up, down=down)
            labels = indexed.labels
            if len(set(labels)) != len(labels):
                return self.space.contract(indexed)
            return indexed
        return self.components[indices]

    def __add__(self, other):
        if isinstance(other, Tensor) and other.rank != self.rank:
            raise ValueError(
                f"Addition requires tensors with the same rank ({self.rank} vs {other.rank})."
            )
        if self.rank == 0:
            if isinstance(other, IndexedTensor) and other.tensor.rank != 0:
                raise ValueError(
                    f"Addition requires tensors with the same rank ({self.rank} vs {other.tensor.rank})."
                )
            if isinstance(other, Tensor):
                return self._as_scalar() + other._as_scalar()
            return self._as_scalar() + other
        if isinstance(other, Tensor):
            if other.space is not self.space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            if other.signature != self.signature:
                raise ValueError("Different signatures; addition requires the same signature.")
            labels = getattr(self, "_labels", None)
            other_labels = getattr(other, "_labels", None)
            if labels is not None or other_labels is not None:
                if labels is None or other_labels is None:
                    raise ValueError("Addition requires tensors with compatible labels.")
                if set(labels) != set(other_labels):
                    raise ValueError("Addition requires tensors with the same labels.")
                if labels != other_labels:
                    perm = [other_labels.index(lab) for lab in labels]
                    other_components = sp.permutedims(other.components, perm)
                else:
                    other_components = other.components
                result = Tensor(self.components + other_components, self.space, signature=self.signature)
                result._labels = list(labels)
                return result
            return Tensor(self.components + other.components, self.space, signature=self.signature)
        return NotImplemented

    def __radd__(self, other):
        if self.rank == 0:
            return other + self._as_scalar()
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Tensor) and other.rank != self.rank:
            raise ValueError(
                f"Subtraction requires tensors with the same rank ({self.rank} vs {other.rank})."
            )
        if self.rank == 0:
            if isinstance(other, IndexedTensor) and other.tensor.rank != 0:
                raise ValueError(
                    f"Subtraction requires tensors with the same rank ({self.rank} vs {other.tensor.rank})."
                )
            if isinstance(other, Tensor):
                return self._as_scalar() - other._as_scalar()
            return self._as_scalar() - other
        if isinstance(other, Tensor):
            if other.space is not self.space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            if other.signature != self.signature:
                raise ValueError("Different signatures; subtraction requires the same signature.")
            labels = getattr(self, "_labels", None)
            other_labels = getattr(other, "_labels", None)
            if labels is not None or other_labels is not None:
                if labels is None or other_labels is None:
                    raise ValueError("Subtraction requires tensors with compatible labels.")
                if set(labels) != set(other_labels):
                    raise ValueError("Subtraction requires tensors with the same labels.")
                if labels != other_labels:
                    perm = [other_labels.index(lab) for lab in labels]
                    other_components = sp.permutedims(other.components, perm)
                else:
                    other_components = other.components
                result = Tensor(self.components - other_components, self.space, signature=self.signature)
                result._labels = list(labels)
                return result
            return Tensor(self.components - other.components, self.space, signature=self.signature)
        return NotImplemented

    def __rsub__(self, other):
        if self.rank == 0:
            return other - self._as_scalar()
        return NotImplemented

    def __mul__(self, other):
        if self.rank == 0:
            scalar = self._as_scalar()
            if isinstance(other, Tensor):
                if other.space is not self.space:
                    raise ValueError("Tensors belong to different TensorSpaces.")
                scaled = scalar * other.components
                return Tensor(scaled, other.space, signature=other.signature)
            if isinstance(other, IndexedTensor):
                if other.tensor.space is not self.space:
                    raise ValueError("Tensors belong to different TensorSpaces.")
                scaled = scalar * other.components
                tensor = Tensor(scaled, other.tensor.space, signature=other.signature)
                indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(other.labels))
                indexed._label_history = set(getattr(other, "_label_history", set()))
                return indexed
            return scalar * other
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) * self.components
            return Tensor(scaled, self.space, signature=self.signature)
        if isinstance(other, Tensor):
            if other.rank == 0:
                scaled = other._as_scalar() * self.components
                return Tensor(scaled, self.space, signature=self.signature)
            if other.space is not self.space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            TP = sp.tensorproduct(self.components, other.components)
            new_sig = self.signature + other.signature
            return Tensor(TP, self.space, signature=new_sig)
        if isinstance(other, IndexedTensor) and hasattr(self, "_labels"):
            indexed = IndexedTensor(self, self.components, self.signature, list(self._labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return self.space.contract(indexed, other)
        return NotImplemented

    def __rmul__(self, other):
        if self.rank == 0:
            return other * self._as_scalar()
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) * self.components
            return Tensor(scaled, self.space, signature=self.signature)
        if isinstance(other, Tensor):
            if other.rank == 0:
                scaled = other._as_scalar() * self.components
                return Tensor(scaled, self.space, signature=self.signature)
            if other.space is not self.space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            TP = sp.tensorproduct(other.components, self.components)
            new_sig = other.signature + self.signature
            return Tensor(TP, self.space, signature=new_sig)
        if isinstance(other, IndexedTensor) and hasattr(self, "_labels"):
            indexed = IndexedTensor(self, self.components, self.signature, list(self._labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return self.space.contract(other, indexed)
        return NotImplemented

    def __truediv__(self, other):
        if self.rank == 0:
            return self._as_scalar() / other
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = self.components / sp.sympify(other)
            return Tensor(scaled, self.space, signature=self.signature)
        return NotImplemented

    def __rtruediv__(self, other):
        if self.rank == 0:
            return other / self._as_scalar()
        return NotImplemented

    def __pow__(self, power):
        if self.rank == 0:
            return self._as_scalar() ** power
        return NotImplemented

    def __neg__(self):
        if self.rank == 0:
            return -self._as_scalar()
        return NotImplemented

    @property
    def comp(self):
        return self.components

    def _move_front_axis_to(self, A, pos):
        rank = A.rank()
        perm = []
        rest = list(range(1, rank))
        for i in range(rank):
            if i == pos:
                perm.append(0)
            else:
                perm.append(rest.pop(0))
        return sp.permutedims(A, perm)

    def _raise_at(self, A, pos):
        if self.space.metric_inv is None:
            raise ValueError("Metric inverse not defined for raising indices.")
        TP = sp.tensorproduct(self.space.metric_inv, A)
        C = sp.tensorcontraction(TP, (1, pos + 2))
        return self._move_front_axis_to(C, pos)

    def _lower_at(self, A, pos):
        if self.space.metric is None:
            raise ValueError("Metric not defined for lowering indices.")
        TP = sp.tensorproduct(self.space.metric.components, A)
        C = sp.tensorcontraction(TP, (1, pos + 2))
        return self._move_front_axis_to(C, pos)

    def as_signature(self, target_signature, simplify=False):
        target_signature = _validate_signature(target_signature, self.rank)
        if target_signature in self._cache:
            return self._cache[target_signature]

        A = self._cache[self.signature]
        sig_cur = list(self.signature)
        for pos in range(self.rank):
            want = target_signature[pos]
            have = sig_cur[pos]
            if have is want:
                continue
            if have is D and want is U:
                A = self._raise_at(A, pos)
                sig_cur[pos] = U
            elif have is U and want is D:
                A = self._lower_at(A, pos)
                sig_cur[pos] = D
            else:
                raise RuntimeError("Impossible state in signature conversion.")

        if simplify:
            A = sp.simplify(A)
        self._cache[target_signature] = A
        return A

    def nabla(self, order=1, deriv_position="prepend"):
        return self.space.nabla(self, order=order, deriv_position=deriv_position)

    def d(self, coord, deriv_position="append"):
        if isinstance(coord, UpIndex):
            raise ValueError("Derivative index must be covariant.")
        if isinstance(coord, (Index, DownIndex)):
            label = coord.name if isinstance(coord, Index) else coord.label
            if label is None or label is NO_LABEL:
                raise ValueError("Derivative index must have an explicit label.")
            coords = self.space.coords
            shape = self.components.shape
            dim = self.space.dim
            if deriv_position == "append":
                new_shape = shape + (dim,)
                flat = []
                for idx in itertools.product(*(range(s) for s in shape)):
                    for k, sym in enumerate(coords):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = self.signature + (D,)
            elif deriv_position == "prepend":
                new_shape = (dim,) + shape
                flat = []
                for k, sym in enumerate(coords):
                    for idx in itertools.product(*(range(s) for s in shape)):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = (D,) + self.signature
            else:
                raise ValueError("deriv_position must be 'append' or 'prepend'.")
            target = sp.ImmutableDenseNDimArray(flat, new_shape)
            out = Tensor(target, self.space, signature=new_sig, name=None, label=self.label)
            out._labels = list(getattr(self, "_labels", [])) + [label] if deriv_position == "append" else [label] + list(getattr(self, "_labels", []))
            return out

        sym = self.space._coord_symbol(coord)
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [sp.diff(v, sym) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = sp.diff(self.components, sym)
        return Tensor(target, self.space, signature=self.signature, name=None, label=self.label)

    def contract(self, pos1, pos2, use_metric=True):
        if pos1 == pos2:
            raise ValueError("pos1 and pos2 must be distinct indices.")
        if not (0 <= pos1 < self.rank and 0 <= pos2 < self.rank):
            raise IndexError("pos1/pos2 out of tensor rank.")

        sig = list(self.signature)
        s1 = sig[pos1]
        s2 = sig[pos2]
        A = self.components

        if s1 is s2:
            if not use_metric:
                raise ValueError("Indices with the same variance require use_metric=True.")
            if s1 is D:
                A = self.as_signature(
                    tuple(U if i == pos2 else s for i, s in enumerate(sig))
                )
                sig[pos2] = U
            else:
                A = self.as_signature(
                    tuple(D if i == pos2 else s for i, s in enumerate(sig))
                )
                sig[pos2] = D

        contracted = sp.tensorcontraction(A, (pos1, pos2))
        new_sig = tuple(s for i, s in enumerate(sig) if i not in (pos1, pos2))
        return Tensor(contracted, self.space, signature=new_sig)

    def idx(self, up=None, down=None):
        rank = self.rank
        if up is None and down is None:
            up = [None] * rank
            down = [None] * rank
        elif up is None or down is None:
            raise ValueError("Provide up and down with the same length as the rank.")

        up = list(up)
        down = list(down)
        if len(up) != rank or len(down) != rank:
            raise ValueError("up/down must have the same length as the tensor rank.")

        labels = []
        target_sig = []
        for i in range(rank):
            up_i = _parse_label(up[i], self.space)
            down_i = _parse_label(down[i], self.space)
            if up_i is not None and down_i is not None:
                raise ValueError("Index cannot be up and down at the same position.")
            if up_i is None and down_i is None:
                target_sig.append(self.signature[i])
                labels.append(self.space._next_label())
            elif up_i is not None:
                target_sig.append(U)
                labels.append(self.space._next_label() if up_i is NO_LABEL else up_i)
            else:
                target_sig.append(D)
                labels.append(self.space._next_label() if down_i is NO_LABEL else down_i)

        A = self.as_signature(tuple(target_sig), simplify=False)
        indexed = IndexedTensor(self, A, tuple(target_sig), labels)
        indexed._label_history = set(getattr(self, "_label_history", set()))
        return indexed

    def up(self, *labels):
        labels = _complete_indices_right(labels, self.rank)
        return _IndexBuilder(self, up=labels, has_up=True)

    def down(self, *labels):
        labels = _complete_indices_right(labels, self.rank)
        return _IndexBuilder(self, down=labels, has_down=True)


class Metric(Tensor):
    pass


class IndexedArray(Tensor):
    def as_signature(self, target_signature, simplify=False):
        target_signature = _validate_signature(target_signature, self.rank)
        if target_signature in self._cache:
            return self._cache[target_signature]
        self._cache[target_signature] = self.components
        return self.components

    def __call__(self, *sig):
        if len(sig) == 1 and isinstance(sig[0], (tuple, list)):
            sig = tuple(sig[0])
        if sig and any(isinstance(s, Index) for s in sig):
            raise TypeError("Use +a/-b for indices with explicit variance.")
        if sig and all(isinstance(s, (UpIndex, DownIndex)) for s in sig):
            if len(sig) != self.rank:
                raise ValueError("Number of indices does not match tensor rank.")
            up = [None] * self.rank
            down = [None] * self.rank
            for i, idx in enumerate(sig):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                else:
                    down[i] = idx.label
            return self.idx(up=up, down=down)
        arr = self.as_signature(sig, simplify=False)
        return IndexedArray(arr, self.space, signature=sig, name=self.name, label=self.label)

    def idx(self, up=None, down=None):
        rank = self.rank
        if up is None and down is None:
            up = [None] * rank
            down = [None] * rank
        elif up is None or down is None:
            raise ValueError("Provide up and down with the same length as the rank.")

        up = list(up)
        down = list(down)
        if len(up) != rank or len(down) != rank:
            raise ValueError("up/down must have the same length as the tensor rank.")

        labels = []
        target_sig = []
        for i in range(rank):
            up_i = _parse_label(up[i], self.space)
            down_i = _parse_label(down[i], self.space)
            if up_i is not None and down_i is not None:
                raise ValueError("Index cannot be up and down at the same position.")
            if up_i is None and down_i is None:
                target_sig.append(self.signature[i])
                labels.append(self.space._next_label())
            elif up_i is not None:
                target_sig.append(U)
                labels.append(self.space._next_label() if up_i is NO_LABEL else up_i)
            else:
                target_sig.append(D)
                labels.append(self.space._next_label() if down_i is NO_LABEL else down_i)

        A = self.as_signature(tuple(target_sig), simplify=False)
        indexed = IndexedArrayItem(self, A, tuple(target_sig), labels)
        indexed._label_history = set(getattr(self, "_label_history", set()))
        return indexed


class IndexedTensor:
    def __init__(self, tensor, components, signature, labels):
        self.tensor = tensor
        self.components = components
        self.signature = signature
        self.labels = labels

    def _repr_latex_(self):
        if hasattr(self.components, "_repr_latex_"):
            return self.components._repr_latex_()
        return sp.latex(self.components)

    def d(self, coord, deriv_position="append"):
        labels = list(self.labels)
        if isinstance(coord, UpIndex):
            raise ValueError("Derivative index must be covariant.")
        if isinstance(coord, Index):
            raise ValueError("Use +a/-b for indices with explicit variance.")
        if isinstance(coord, DownIndex):
            lab = coord.label
            if lab is None or lab is NO_LABEL:
                raise ValueError("Derivative index must have an explicit label.")
            coords = self.tensor.space.coords
            shape = self.components.shape
            dim = self.tensor.space.dim
            if deriv_position == "append":
                new_shape = shape + (dim,)
                flat = []
                for idx in itertools.product(*(range(s) for s in shape)):
                    for k, sym in enumerate(coords):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = self.signature + (D,)
                new_labels = labels + [lab]
            elif deriv_position == "prepend":
                new_shape = (dim,) + shape
                flat = []
                for k, sym in enumerate(coords):
                    for idx in itertools.product(*(range(s) for s in shape)):
                        flat.append(sp.diff(self.components[idx], sym))
                new_sig = (D,) + self.signature
                new_labels = [lab] + labels
            else:
                raise ValueError("deriv_position must be 'append' or 'prepend'.")
            target = sp.ImmutableDenseNDimArray(flat, new_shape)
            tensor = Tensor(target, self.tensor.space, signature=new_sig)
            return IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)

        sym = self.tensor.space._coord_symbol(coord)
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [sp.diff(v, sym) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = sp.diff(self.components, sym)
        tensor = Tensor(target, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, labels)

    def __repr__(self):
        return repr(self.components)

    def fmt(self, expr=None):
        if expr is None:
            if self.tensor.rank == 0:
                target = sp.expand(sp.simplify(self.tensor._as_scalar()))
            elif isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
                arr = sp.ImmutableDenseNDimArray(self.components)
                target = arr.applyfunc(lambda v: sp.expand(sp.simplify(v)))
            else:
                target = sp.expand(sp.simplify(self.components))
            tensor = Tensor(target, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        if isinstance(expr, Tensor):
            return expr.fmt()
        if isinstance(expr, IndexedTensor):
            return expr.fmt()
        return sp.expand(sp.simplify(expr))

    def subs(self, *args, **kwargs):
        if isinstance(self.components, (sp.Array, sp.ImmutableDenseNDimArray)):
            flat = [v.subs(*args, **kwargs) for v in self.components]
            target = sp.ImmutableDenseNDimArray(flat, self.components.shape)
        else:
            target = self.components.subs(*args, **kwargs)
        tensor = Tensor(target, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __eq__(self, other):
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
        else:
            return NotImplemented
        if other_space is not self.tensor.space:
            raise ValueError("Tensors belong to different TensorSpaces.")
        if other_sig != self.signature:
            raise ValueError("Different signatures; equality requires the same signature.")
        return self.components == other_components

    def __call__(self, *idx):
        rank = len(self.signature)
        if len(idx) > rank:
            raise ValueError("Number of indices does not match tensor rank.")
        if len(idx) == rank:
            return self.components[idx]
        slicer = idx + (slice(None),) * (rank - len(idx))
        return self.components[slicer]

    def __getitem__(self, indices):
        if not isinstance(indices, tuple):
            indices = (indices,)
        if any(isinstance(idx, (UpIndex, DownIndex, Index)) for idx in indices):
            if any(isinstance(idx, Index) for idx in indices):
                raise TypeError("Use +a/-b for indices with explicit variance.")
            if not all(isinstance(idx, (UpIndex, DownIndex)) for idx in indices):
                raise TypeError("Use only +a/-b (or U(a)/D(b)) to index the tensor.")
            if len(indices) != len(self.signature):
                raise ValueError("Number of indices does not match tensor rank.")
            up = [None] * len(self.signature)
            down = [None] * len(self.signature)
            for i, idx in enumerate(indices):
                if isinstance(idx, UpIndex):
                    up[i] = idx.label
                else:
                    down[i] = idx.label
            indexed = self.tensor.idx(up=up, down=down)
            history = set(getattr(indexed, "_label_history", set()))
            history.update(getattr(self, "_label_history", set()))
            indexed._label_history = history
            labels = indexed.labels
            if len(set(labels)) != len(labels):
                return self.tensor.space.contract(indexed)
            return indexed
        return self.components[indices]

    def get(self, *idx):
        return self.__call__(*idx)

    def _resolve_position(self, idx):
        if isinstance(idx, int):
            if not (0 <= idx < len(self.signature)):
                raise IndexError("Index out of tensor rank.")
            return idx
        if isinstance(idx, (UpIndex, DownIndex)):
            label = idx.label
        elif isinstance(idx, Index):
            raise ValueError("Use +a/-b for indices with explicit variance.")
        else:
            raise ValueError("Use +a/-b for indices with explicit variance.")
        matches = [i for i, lab in enumerate(self.labels) if lab == label]
        if len(matches) != 1:
            raise ValueError(f"Index {label!r} not found or duplicated.")
        return matches[0]

    def _swap_axes(self, pos1, pos2):
        perm = list(range(len(self.signature)))
        perm[pos1], perm[pos2] = perm[pos2], perm[pos1]
        return sp.permutedims(self.components, perm)

    def symmetric(self, idx1, idx2):
        pos1 = self._resolve_position(idx1)
        pos2 = self._resolve_position(idx2)
        if pos1 == pos2:
            raise ValueError("Indices must be distinct.")
        if self.signature[pos1] is not self.signature[pos2]:
            raise ValueError("Indices with different variance cannot be symmetrized.")
        swapped = self._swap_axes(pos1, pos2)
        arr = sp.Rational(1, 2) * (self.components + swapped)
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def antisymmetric(self, idx1, idx2):
        pos1 = self._resolve_position(idx1)
        pos2 = self._resolve_position(idx2)
        if pos1 == pos2:
            raise ValueError("Indices must be distinct.")
        if self.signature[pos1] is not self.signature[pos2]:
            raise ValueError("Indices with different variance cannot be antisymmetrized.")
        swapped = self._swap_axes(pos1, pos2)
        arr = sp.Rational(1, 2) * (self.components - swapped)
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __mul__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = other * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, Tensor) and other.rank == 0:
            scaled = other._as_scalar() * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, IndexedTensor):
            space = self.tensor.space
            if other.tensor.space is not space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            history = set(getattr(self, "_label_history", set()))
            other_history = set(getattr(other, "_label_history", set()))
            reused = history & set(other.labels)
            if reused:
                raise ValueError(f"Index {sorted(reused)[0]} reused after contraction.")
            reused = other_history & set(self.labels)
            if reused:
                raise ValueError(f"Index {sorted(reused)[0]} reused after contraction.")
            if set(self.labels) & set(other.labels):
                return space.contract(self, other)
            TP = sp.tensorproduct(self.components, other.components)
            new_sig = self.signature + other.signature
            new_labels = list(self.labels) + list(other.labels)
            tensor = Tensor(TP, space, signature=new_sig)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)
            indexed._label_history = history | other_history
            return indexed
        if isinstance(other, Tensor) and hasattr(other, "_labels"):
            space = self.tensor.space
            if other.space is not space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            indexed = IndexedTensor(other, other.components, other.signature, list(other._labels))
            indexed._label_history = set(getattr(other, "_label_history", set()))
            return space.contract(self, indexed)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = other * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, Tensor) and other.rank == 0:
            scaled = other._as_scalar() * self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
            indexed._label_history = set(getattr(self, "_label_history", set()))
            return indexed
        if isinstance(other, IndexedTensor):
            space = other.tensor.space
            if self.tensor.space is not space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            history = set(getattr(self, "_label_history", set()))
            other_history = set(getattr(other, "_label_history", set()))
            reused = history & set(other.labels)
            if reused:
                raise ValueError(f"Index {sorted(reused)[0]} reused after contraction.")
            reused = other_history & set(self.labels)
            if reused:
                raise ValueError(f"Index {sorted(reused)[0]} reused after contraction.")
            if set(self.labels) & set(other.labels):
                return space.contract(other, self)
            TP = sp.tensorproduct(other.components, self.components)
            new_sig = other.signature + self.signature
            new_labels = list(other.labels) + list(self.labels)
            tensor = Tensor(TP, space, signature=new_sig)
            indexed = IndexedTensor(tensor, tensor.components, tensor.signature, new_labels)
            indexed._label_history = history | other_history
            return indexed
        if isinstance(other, Tensor) and hasattr(other, "_labels"):
            space = other.space
            if self.tensor.space is not space:
                raise ValueError("Tensores pertencem a TensorSpaces distintos.")
            indexed = IndexedTensor(other, other.components, other.signature, list(other._labels))
            return space.contract(indexed, self)
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, sp.Basic) and not isinstance(other, (Tensor, IndexedTensor)):
            if len(self.signature) == 0:
                return self.components[()] + other
            return NotImplemented
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
            other_labels = list(other.labels)
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
            other_labels = list(getattr(other, "_labels", []))
        else:
            return NotImplemented
        if len(other_sig) != len(self.signature):
            raise ValueError(
                f"Addition requires tensors with the same rank ({len(self.signature)} vs {len(other_sig)})."
            )
        if other_space is not self.tensor.space:
            raise ValueError("Tensors belong to different TensorSpaces.")
        labels = list(self.labels)
        if other_labels:
            if set(other_labels) != set(labels):
                raise ValueError("Addition requires the same labels.")
            perm = [other_labels.index(lab) for lab in labels]
            other_components = sp.permutedims(other_components, perm)
            other_sig = tuple(other_sig[i] for i in perm)
        if other_sig != self.signature:
            raise ValueError("Different signatures; addition requires the same signature.")
        arr = self.components + other_components
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, IndexedTensor):
            other_sig = other.signature
            other_space = other.tensor.space
            other_components = other.components
            other_labels = list(other.labels)
        elif isinstance(other, Tensor):
            other_sig = other.signature
            other_space = other.space
            other_components = other.components
            other_labels = list(getattr(other, "_labels", []))
        else:
            return NotImplemented
        if len(other_sig) != len(self.signature):
            raise ValueError(
                f"Subtraction requires tensors with the same rank ({len(self.signature)} vs {len(other_sig)})."
            )
        if other_space is not self.tensor.space:
            raise ValueError("Tensors belong to different TensorSpaces.")
        labels = list(self.labels)
        if other_labels:
            if set(other_labels) != set(labels):
                raise ValueError("Subtraction requires the same labels.")
            perm = [other_labels.index(lab) for lab in labels]
            other_components = sp.permutedims(other_components, perm)
            other_sig = tuple(other_sig[i] for i in perm)
        if other_sig != self.signature:
            raise ValueError("Different signatures; subtraction requires the same signature.")
        arr = self.components - other_components
        tensor = Tensor(arr, self.tensor.space, signature=self.signature)
        return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))

    def __rsub__(self, other):
        if not isinstance(other, IndexedTensor):
            return NotImplemented
        return other.__sub__(self)

    def __truediv__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = self.components / sp.sympify(other)
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        return NotImplemented

    def __rtruediv__(self, other):
        if isinstance(other, (numbers.Number, sp.Basic)) and not isinstance(
            other, (Tensor, IndexedTensor)
        ):
            scaled = sp.sympify(other) / self.components
            tensor = Tensor(scaled, self.tensor.space, signature=self.signature)
            return IndexedTensor(tensor, tensor.components, tensor.signature, list(self.labels))
        return NotImplemented


class IndexedArrayItem(IndexedTensor):
    def __eq__(self, other):
        if isinstance(other, IndexedTensor):
            if other.tensor.space is not self.tensor.space:
                raise ValueError("Tensors belong to different TensorSpaces.")
            return self.components == other.components
        return NotImplemented


class TensorFactory:
    def __init__(self, space):
        self.space = space

    def __call__(self, tensor, index=None, name=None, label=None):
        from .core import TensorSpace

        return TensorSpace.tensor(self.space, tensor, index=index, name=name, label=label)

    def coord_index(self, names):
        return self.space.coord_index(names)

    def from_function(self, func, signature, name=None, label=None):
        return self.space.from_function(func, signature, name=name, label=label)

    def from_array(self, array, signature, name=None, label=None):
        return self.space.from_array(array, signature, name=name, label=label)

    def generic(self, name, signature, coords=None, label=None):
        return self.space.generic(name, signature, coords=coords, label=label)

    def zeros(self, signature, name=None, label=None):
        return self.space.zeros(signature, name=name, label=label)

    def scalar(self, expr, name=None, label=None):
        return self.space.scalar(expr, name=name, label=label)


class _IndexBuilder:
    def __init__(self, tensor, up=None, down=None, has_up=False, has_down=False):
        self.tensor = tensor
        self.up = [None] * tensor.rank if up is None else list(up)
        self.down = [None] * tensor.rank if down is None else list(down)
        self.has_up = has_up
        self.has_down = has_down

    def up(self, *labels):
        labels = _complete_indices_right(labels, self.tensor.rank)
        if self.has_down:
            return self.tensor.idx(up=labels, down=self.down)
        return _IndexBuilder(self.tensor, up=labels, down=self.down, has_up=True, has_down=self.has_down)

    def down(self, *labels):
        labels = _complete_indices_right(labels, self.tensor.rank)
        if self.has_up:
            return self.tensor.idx(up=self.up, down=labels)
        return _IndexBuilder(self.tensor, up=self.up, down=labels, has_up=self.has_up, has_down=True)


def _parse_label(label, space):
    if label is NO_LABEL:
        return NO_LABEL
    if label in ("_", ".", "empty", None):
        return None
    if isinstance(label, Index):
        return label.name
    if isinstance(label, str):
        return label.strip()
    return str(label)


def _complete_indices_right(labels, rank):
    labels = list(labels)
    if len(labels) > rank:
        raise ValueError("Number of indices does not match tensor rank.")
    labels.extend([None] * (rank - len(labels)))
    return labels


def _parse_tensor_token(token):
    name = ""
    seq = []
    i = 0
    while i < len(token) and token[i].isalnum():
        name += token[i]
        i += 1
    while i < len(token):
        if token[i] in ("^", "_"):
            var = token[i]
            i += 1
            if i < len(token) and token[i] == "{":
                block, i = _read_block(token, i)
                labels = _split_indices(block)
            else:
                start = i
                while i < len(token) and token[i].isalnum():
                    i += 1
                if start == i:
                    raise ValueError("Expected an index after '^' or '_'.")
                labels = [token[start:i]]
            for lab in labels:
                seq.append((var, lab))
        else:
            i += 1
    return name, seq


def _expand_indices(rank, up_labels=None, down_labels=None):
    if down_labels is None and up_labels is not None:
        if all(isinstance(item, tuple) and len(item) == 2 for item in up_labels):
            seq = list(up_labels)
            if len(seq) != rank:
                raise ValueError("Number of indices does not match tensor rank.")
            up_full = [None] * rank
            down_full = [None] * rank
            for i, (var, lab) in enumerate(seq):
                if var == "^":
                    up_full[i] = lab
                elif var == "_":
                    down_full[i] = lab
                else:
                    raise ValueError(f"Invalid variance: {var!r}. Use '^' or '_'.")
            return up_full, down_full
    up_labels = [] if up_labels is None else list(up_labels)
    down_labels = [] if down_labels is None else list(down_labels)
    if len(up_labels) + len(down_labels) != rank:
        raise ValueError("Number of indices does not match tensor rank.")
    up_full = [None] * rank
    down_full = [None] * rank
    for i, lab in enumerate(up_labels):
        up_full[i] = lab
    for i, lab in enumerate(down_labels):
        down_full[len(up_labels) + i] = lab
    return up_full, down_full


def _read_block(s, i):
    if s[i] != "{":
        raise ValueError("Expected '{' in index expression.")
    depth = 0
    start = i + 1
    i += 1
    while i < len(s):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            if depth == 0:
                return s[start:i], i + 1
            depth -= 1
        i += 1
    raise ValueError("Index block not closed.")


def _split_indices(block):
    out = []
    for part in block.split(","):
        part = part.strip()
        if part in ("", "_", ".", "empty"):
            out.append(NO_LABEL)
        else:
            out.append(part)
    return out


__all__ = [
    "CoordIndex",
    "D",
    "Down",
    "DownIndex",
    "Index",
    "IndexedArray",
    "IndexedTensor",
    "Metric",
    "NO_LABEL",
    "Tensor",
    "TensorFactory",
    "U",
    "Up",
    "UpIndex",
    "d",
    "table",
    "u",
]
