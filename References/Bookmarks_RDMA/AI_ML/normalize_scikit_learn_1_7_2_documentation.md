# normalize — scikit-learn 1.7.2 documentation

- **Source:** https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.normalize.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# normalize[#](#normalize)

- 
sklearn.preprocessing.normalize(*X*, *norm='l2'*, *\**, *axis=1*, *copy=True*, *return\_norm=False*)[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/preprocessing/_data.py#L1968)[#](#sklearn.preprocessing.normalize)
- Scale input vectors individually to unit norm (vector length). Read more in the [User Guide](../preprocessing.html#preprocessing-normalization).
  - Parameters:
    - **X**{array-like, sparse matrix} of shape (n\_samples, n\_features)
    - The data to normalize, element by element. scipy.sparse matrices should be in CSR format to avoid an un-necessary copy.
    - **norm**{‘l1’, ‘l2’, ‘max’}, default=’l2’
    - The norm to use to normalize each non zero sample (or each non-zero feature if axis is 0).
    - **axis**{0, 1}, default=1
    - Define axis used to normalize the data along. If 1, independently normalize each sample, otherwise (if 0) normalize each feature.
    - **copy**bool, default=True
    - If False, try to avoid a copy and normalize in place. This is not guaranteed to always work in place; e.g. if the data is a numpy array with an int dtype, a copy will be returned even with copy=False.
    - **return\_norm**bool, default=False
    - Whether to return the computed norms.
  - Returns:
    - **X**{ndarray, sparse matrix} of shape (n\_samples, n\_features)
    - Normalized input X.
    - **norms**ndarray of shape (n\_samples, ) if axis=1 else (n\_features, )
    - An array of norms along given axis for X. When X is sparse, a NotImplementedError will be raised for norm ‘l1’ or ‘l2’.
See also 
  - [`Normalizer`](sklearn.preprocessing.Normalizer.html#sklearn.preprocessing.Normalizer)
  - Performs normalization using the Transformer API (e.g. as part of a preprocessing [`Pipeline`](sklearn.pipeline.Pipeline.html#sklearn.pipeline.Pipeline)).
Notes For a comparison of the different scalers, transformers, and normalizers,
see: [Compare the effect of different scalers on data with outliers](../../auto_examples/preprocessing/plot_all_scaling.html#sphx-glr-auto-examples-preprocessing-plot-all-scaling-py).
Examples \>>> from sklearn.preprocessing import normalize >>> X = \[\[-2, 1, 2\], \[-1, 0, 1\]\] >>> normalize(X, norm="l1") # L1 normalization each row independently array(\[\[-0.4, 0.2, 0.4\], \[-0.5, 0. , 0.5\]\]) >>> normalize(X, norm="l2") # L2 normalization each row independently array(\[\[-0.67, 0.33, 0.67\], \[-0.71, 0. , 0.71\]\])