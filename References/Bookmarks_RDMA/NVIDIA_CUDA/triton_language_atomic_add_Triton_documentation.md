# triton.language.atomic_add — Triton documentation

- **Source:** https://triton-lang.org/main/python-api/generated/triton.language.atomic_add.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > NVIDIA & CUDA)
- **Retrieved:** 2026-10-22


---

# triton.language.atomic\_add[](#triton-language-atomic-add)

- 
triton.language.atomic\_add(*pointer*, *val*, *mask=None*, *sem=None*, *scope=None*, *\_semantic=None*)[](#triton.language.atomic_add)
- Performs an atomic add at the memory location specified by `pointer`.
Return the data stored at `pointer` before the atomic operation.
  - Parameters:
    - **pointer** (*Block of dtype=triton.PointerDType*) – The memory locations to operate on
    - **val** (*Block of dtype=pointer.dtype.element\_ty*) – The values with which to perform the atomic operation
    - **sem** (*str, optional*) – Specifies the memory semantics for the operation. Acceptable values are “acquire”,
“release”, “acq\_rel” (stands for “ACQUIRE\_RELEASE”), and “relaxed”. If not provided,
the function defaults to using “acq\_rel” semantics.
    - **scope** (*str, optional*) – Defines the scope of threads that observe the synchronizing effect of the atomic operation.
Acceptable values are “gpu” (default), “cta” (cooperative thread array, thread block), or “sys” (stands for “SYSTEM”). The default value is “gpu”.
This function can also be called as a member function on [`tensor`](triton.language.tensor.html#triton.language.tensor),
as `x.atomic_add(...)` instead of `atomic_add(x, ...)`.