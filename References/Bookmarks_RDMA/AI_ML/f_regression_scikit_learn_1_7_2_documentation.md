# f_regression — scikit-learn 1.7.2 documentation

- **Source:** https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.f_regression.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# f\_regression[#](#f-regression)

- 
sklearn.feature\_selection.f\_regression(*X*, *y*, *\**, *center=True*, *force\_finite=True*)[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/feature_selection/_univariate_selection.py#L397)[#](#sklearn.feature_selection.f_regression)
- Univariate linear regression tests returning F-statistic and p-values. Quick linear model for testing the effect of a single regressor, sequentially for many regressors. This is done in 2 steps: 
  1. The cross correlation between each regressor and the target is computed
using [`r_regression`](sklearn.feature_selection.r_regression.html#sklearn.feature_selection.r_regression) as:
E\[(X\[:, i\] - mean(X\[:, i\])) \* (y - mean(y))\] / (std(X\[:, i\]) \* std(y))
  2. It is converted to an F score and then to a p-value.
[`f_regression`](#sklearn.feature_selection.f_regression) is derived from [`r_regression`](sklearn.feature_selection.r_regression.html#sklearn.feature_selection.r_regression) and will rank
features in the same order if all the features are positively correlated
with the target.
Note however that contrary to [`f_regression`](#sklearn.feature_selection.f_regression), [`r_regression`](sklearn.feature_selection.r_regression.html#sklearn.feature_selection.r_regression) values lie in \[-1, 1\] and can thus be negative. [`f_regression`](#sklearn.feature_selection.f_regression) is
therefore recommended as a feature selection criterion to identify
potentially predictive feature for a downstream classifier, irrespective of
the sign of the association with the target variable.
Furthermore [`f_regression`](#sklearn.feature_selection.f_regression) returns p-values while [`r_regression`](sklearn.feature_selection.r_regression.html#sklearn.feature_selection.r_regression) does not.
Read more in the [User Guide](../feature_selection.html#univariate-feature-selection).
  - Parameters:
    - **X**{array-like, sparse matrix} of shape (n\_samples, n\_features)
    - The data matrix.
    - **y**array-like of shape (n\_samples,)
    - The target vector.
    - **center**bool, default=True
    - Whether or not to center the data matrix `X` and the target vector `y`.
By default, `X` and `y` will be centered.
    - **force\_finite**bool, default=True
    - Whether or not to force the F-statistics and associated p-values to be finite. There are two cases where the F-statistic is expected to not be finite: 
      - when the target `y` or some features in `X` are constant. In this
case, the Pearson’s R correlation is not defined leading to obtain `np.nan` values in the F-statistic and p-value. When `force_finite=True`, the F-statistic is set to `0.0` and the
associated p-value is set to `1.0`.
      - when a feature in `X` is perfectly correlated (or
anti-correlated) with the target `y`. In this case, the F-statistic
is expected to be `np.inf`. When `force_finite=True`, the F-statistic
is set to `np.finfo(dtype).max` and the associated p-value is set to `0.0`.
Added in version 1.1.
  - Returns:
    - **f\_statistic**ndarray of shape (n\_features,)
    - F-statistic for each feature.
    - **p\_values**ndarray of shape (n\_features,)
    - P-values associated with the F-statistic.
See also 
  - [`r_regression`](sklearn.feature_selection.r_regression.html#sklearn.feature_selection.r_regression)
  - Pearson’s R between label/feature for regression tasks.
  - [`f_classif`](sklearn.feature_selection.f_classif.html#sklearn.feature_selection.f_classif)
  - ANOVA F-value between label/feature for classification tasks.
  - [`chi2`](sklearn.feature_selection.chi2.html#sklearn.feature_selection.chi2)
  - Chi-squared stats of non-negative features for classification tasks.
  - [`SelectKBest`](sklearn.feature_selection.SelectKBest.html#sklearn.feature_selection.SelectKBest)
  - Select features based on the k highest scores.
  - [`SelectFpr`](sklearn.feature_selection.SelectFpr.html#sklearn.feature_selection.SelectFpr)
  - Select features based on a false positive rate test.
  - [`SelectFdr`](sklearn.feature_selection.SelectFdr.html#sklearn.feature_selection.SelectFdr)
  - Select features based on an estimated false discovery rate.
  - [`SelectFwe`](sklearn.feature_selection.SelectFwe.html#sklearn.feature_selection.SelectFwe)
  - Select features based on family-wise error rate.
  - [`SelectPercentile`](sklearn.feature_selection.SelectPercentile.html#sklearn.feature_selection.SelectPercentile)
  - Select features based on percentile of the highest scores.
Examples \>>> from sklearn.datasets import make\_regression >>> from sklearn.feature\_selection import f\_regression >>> X, y = make\_regression( ... n\_samples=50, n\_features=3, n\_informative=1, noise=1e-4, random\_state=42 ... ) >>> f\_statistic, p\_values = f\_regression(X, y) >>> f\_statistic array(\[1.21, 2.67e13, 2.66\]) >>> p\_values array(\[0.276, 1.54e-283, 0.11\])

## Gallery examples[#](#gallery-examples)

[Feature agglomeration vs. univariate selection](../../auto_examples/cluster/plot_feature_agglomeration_vs_univariate_selection.html)

[Comparison of F-test and mutual information](../../auto_examples/feature_selection/plot_f_test_vs_mi.html)