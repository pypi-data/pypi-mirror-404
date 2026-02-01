"""
PIANO: Probabilistic Inference Autoencoder Networks for multi-Omics
Copyright (C) 2025 Ning Wang

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# test_triton_sparse.py
import numpy as np
import pytest
import torch
from scipy import sparse as sp

# import the module you wrote above
from piano.utils.triton_sparse import SparseTritonMatrix 


CUDA_AVAILABLE = torch.cuda.is_available()
pytestmark = pytest.mark.skipif(
    not CUDA_AVAILABLE, reason="GPU with CUDA required for Triton kernels"
)


# ---------------------------------------------------------------------------
# Helper: create a random CSR matrix with controllable shape / density
# ---------------------------------------------------------------------------
def make_random_csr(n_rows, n_cols, density=0.05, seed=0):
    rng = np.random.default_rng(seed)
    nnz = int(n_rows * n_cols * density)
    row = rng.integers(0, n_rows, size=nnz, dtype=np.int32)
    col = rng.integers(0, n_cols, size=nnz, dtype=np.int32)
    data = rng.random(size=nnz, dtype=np.float32)
    return sp.csr_matrix((data, (row, col)), shape=(n_rows, n_cols))


# ---------------------------------------------------------------------------
# Parametrised test cases
#
#   * small_cols → indices should be uint16  (≤ 65 535)
#   * large_cols → indices should be int32   (>  65 535, < 2³¹)
# ---------------------------------------------------------------------------
CASES = [
    pytest.param(
        dict(n_rows=256, n_cols=50_000, density=0.03),
        torch.uint16 if hasattr(torch, "uint16") else torch.int16,
        id="uint16_indices",
    ),
    pytest.param(
        dict(n_rows=256, n_cols=70_000, density=0.03),
        torch.int32,
        id="int32_indices",
    ),
]


@pytest.mark.parametrize("csr_kwargs, expected_idx_dtype", CASES)
def test_sparse_cuda_matrix_correctness(csr_kwargs, expected_idx_dtype):
    """Compare Triton result with reference SciPy for various index widths."""
    X = make_random_csr(**csr_kwargs)
    sm = SparseTritonMatrix(X)

    # ---- dtype assertions -------------------------------------------------
    assert sm.indices.dtype == expected_idx_dtype
    assert sm.indptr.dtype == torch.int32  # indptr stays i32 for these sizes

    # ---- numerical equality ----------------------------------------------
    rng = np.random.default_rng(42)
    for _ in range(5):  # five random batches
        rows = rng.integers(0, X.shape[0], size=64, dtype=np.int64)
        dense_gpu = sm[rows].cpu().numpy()
        dense_ref = X[rows, :].toarray()
        np.testing.assert_allclose(dense_gpu, dense_ref, rtol=0, atol=0)


