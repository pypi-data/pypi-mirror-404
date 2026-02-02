from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn


def _shape_of(x: Any) -> Any:
    """Return nested shapes for tensors / containers. Leaves other types as type name."""
    if torch.is_tensor(x):
        return tuple(x.shape)
    if isinstance(x, (list, tuple)):
        return type(x)([_shape_of(v) for v in x])
    if isinstance(x, dict):
        return {k: _shape_of(v) for k, v in x.items()}
    return type(x).__name__


@dataclass
class LayerRecord:
    name: str
    type: str
    in_shape: Any
    out_shape: Any
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyzeResult:
    records: List[LayerRecord]
    error: Optional[str] = None
    error_layer: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


def analyze(model: nn.Module, *example_inputs: Any, device: Optional[str] = None) -> AnalyzeResult:
    model = model.eval()
    if device:
        model = model.to(device)

    # map module object -> qualified name
    name_map = {m: n for n, m in model.named_modules()}
    records: List[LayerRecord] = []
    handles = []
    current_module: Dict[str, Optional[nn.Module]] = {"mod": None}

    def hook(mod: nn.Module, inp: Tuple[Any, ...], out: Any):
        # skip root module to avoid a noisy first row
        if mod is model:
            return

        n = name_map.get(mod, mod.__class__.__name__)
        in_obj = inp[0] if len(inp) == 1 else inp

        rec = LayerRecord(
            name=n,
            type=mod.__class__.__name__,
            in_shape=_shape_of(in_obj),
            out_shape=_shape_of(out),
            extra={},
        )

        # add a bit of metadata for hints
        if isinstance(mod, nn.Linear):
            rec.extra.update(in_features=mod.in_features, out_features=mod.out_features)
        if isinstance(mod, nn.Conv2d):
            rec.extra.update(
                in_channels=mod.in_channels,
                out_channels=mod.out_channels,
                kernel_size=mod.kernel_size,
            )
        if isinstance(mod, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)):
            rec.extra.update(num_features=mod.num_features)

        records.append(rec)
        current_module["mod"] = None

    def pre_hook(mod: nn.Module, inp: Tuple[Any, ...]):
        if mod is model:
            return
        # track most recent module whose forward started
        current_module["mod"] = mod

    # register hooks on all submodules
    for m in model.modules():
        if m is model:
            continue
        handles.append(m.register_forward_pre_hook(pre_hook))
        handles.append(m.register_forward_hook(hook))

    error = None
    error_layer = None
    with torch.no_grad():
        try:
            model(*example_inputs)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            mod = current_module.get("mod")
            if mod is not None:
                error_layer = name_map.get(mod, mod.__class__.__name__)

    for h in handles:
        h.remove()

    if error and error_layer:
        error = f"{error} (layer: {error_layer})"

    suggestions = suggest_fixes(records, error)
    return AnalyzeResult(records=records, error=error, error_layer=error_layer, suggestions=suggestions)


def suggest_fixes(records: List[LayerRecord], error: Optional[str]) -> List[str]:
    tips: List[str] = []

    # Linear mismatch
    for r in reversed(records):
        if r.type == "Linear" and isinstance(r.in_shape, tuple) and len(r.in_shape) >= 2:
            got = r.in_shape[-1]
            expected = r.extra.get("in_features")
            if isinstance(expected, int) and got != expected:
                tips.append(
                    f"[{r.name}] Linear expects in_features={expected} but got last_dim={got}. "
                    f"Fix: set in_features={got}, or reshape/flatten before this layer."
                )
                if len(r.in_shape) == 4:
                    tips.append(
                        f"[{r.name}] Input is 4D {r.in_shape}. "
                        f"Common fix: add nn.Flatten(start_dim=1) before Linear."
                    )
                break

    # Conv2d channel mismatch (assume NCHW)
    for r in reversed(records):
        if r.type == "Conv2d" and isinstance(r.in_shape, tuple):
            if len(r.in_shape) == 4:
                got_c = r.in_shape[1]
                expected_c = r.extra.get("in_channels")
                if isinstance(expected_c, int) and got_c != expected_c:
                    tips.append(
                        f"[{r.name}] Conv2d expects in_channels={expected_c} but got C={got_c} (assuming NCHW). "
                        f"Fix: set in_channels={got_c}, permute NHWC->NCHW, or add a 1x1 conv adapter."
                    )
                    break
            else:
                tips.append(
                    f"[{r.name}] Conv2d received {r.in_shape} but expects 4D (N,C,H,W). "
                    f"Fix: reshape/unsqueeze or check your data pipeline."
                )
                break

    # BatchNorm2d expects 4D
    for r in reversed(records):
        if r.type == "BatchNorm2d" and isinstance(r.in_shape, tuple) and len(r.in_shape) != 4:
            tips.append(
                f"[{r.name}] BatchNorm2d expects 4D (N,C,H,W) but got {r.in_shape}. "
                f"Fix: use BatchNorm1d for (N,F)/(N,C,L) or reshape to NCHW."
            )
            break

    if error:
        tips.append(f"Runtime error observed: {error}")
        tips.append("Tip: inspect the last 5 recorded layers — the mismatch is usually right after them.")

    return tips


def print_report(result: AnalyzeResult, last_n: int = 50) -> None:
    recs = result.records[-last_n:]
    for r in recs:
        extras = (" " + str(r.extra)) if r.extra else ""
        print(
            f"{r.name:40} {r.type:15} {str(r.in_shape):18} -> {str(r.out_shape):18}{extras}"
        )

    if result.error:
        print("\n--- ERROR ---")
        print(result.error)
        if result.error_layer:
            print(f"Layer: {result.error_layer}")

    if result.suggestions:
        print("\n--- SUGGESTIONS ---")
        for s in result.suggestions:
            print("-", s)


def count_parameters(model: nn.Module, trainable_only: bool = True) -> int:
    """Count model parameters.

    Args:
        model: PyTorch module.
        trainable_only: If True, count only parameters that require gradients.
    """
    if trainable_only:
        return sum(p.numel() for p in model.parameters() if p.requires_grad)
    return sum(p.numel() for p in model.parameters())


__all__ = [
    "LayerRecord",
    "AnalyzeResult",
    "analyze",
    "suggest_fixes",
    "print_report",
    "count_parameters",
]
