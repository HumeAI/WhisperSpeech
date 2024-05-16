# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/D. Common inference utilities.ipynb.

# %% auto 0
__all__ = ['get_compute_device']

# %% ../nbs/D. Common inference utilities.ipynb 1
import torch
import torch.nn.functional as F

from contextlib import nullcontext

# %% ../nbs/D. Common inference utilities.ipynb 2
def get_default_compute_device():
    if torch.cuda.is_available() and (torch.version.cuda or torch.version.hip):
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'

preferred_device = None

# %% ../nbs/D. Common inference utilities.ipynb 3
def get_compute_device():
    global preferred_device
    if preferred_device is None: preferred_device = get_default_compute_device()
    return preferred_device

# %% ../nbs/D. Common inference utilities.ipynb 4
def load_model(ref=None, spec=None, device='cpu'):
    if spec is not None: return spec
    if ":" in ref:
        repo_id, filename = ref.split(":", 1)
        local_filename = hf_hub_download(repo_id=repo_id, filename=filename)
    else:
        local_filename = ref
    return torch.load(local_filename, map_location=device)

# %% ../nbs/D. Common inference utilities.ipynb 5
def inference_context():
    if torch.cuda.is_available():
        return torch.backends.cuda.sdp_kernel(enable_flash=False, enable_mem_efficient=False, enable_math=True)
    else:
        return nullcontext()

# from https://github.com/pytorch-labs/gpt-fast/blob/main/generate.py
def multinomial_sample_one_no_sync(probs_sort): # Does multinomial sampling without a cuda synchronization
    q = torch.empty_like(probs_sort).exponential_(1)
    return torch.argmax(probs_sort / q, dim=-1, keepdim=True).to(dtype=torch.int)

def logits_to_probs(logits, T=1.0, top_k=None):
    logits = logits / max(T, 1e-5)

    if top_k is not None:
        v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        pivot = v.select(-1, -1).unsqueeze(-1)
        logits = torch.where(logits < pivot, -float("Inf"), logits)

    probs = torch.nn.functional.softmax(logits, dim=-1)
    return probs

def sample(logits, T=1.0, top_k=None):
    probs = logits_to_probs(logits, T, top_k)
    idx_next = multinomial_sample_one_no_sync(probs)
    return idx_next
