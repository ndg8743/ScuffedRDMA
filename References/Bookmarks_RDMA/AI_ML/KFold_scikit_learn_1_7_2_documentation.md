# KFold — scikit-learn 1.7.2 documentation

- **Source:** https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# KFold[#](#kfold)

- 
class sklearn.model\_selection.KFold(*n\_splits=5*, *\**, *shuffle=False*, *random\_state=None*)[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/model_selection/_split.py#L437)[#](#sklearn.model_selection.KFold)
- K-Fold cross-validator. Provides train/test indices to split data in train/test sets. Split dataset into k consecutive folds (without shuffling by default). Each fold is then used once as a validation while the k - 1 remaining folds form the training set. Read more in the [User Guide](../cross_validation.html#k-fold).
For visualisation of cross-validation behaviour and
comparison between common scikit-learn split methods
refer to [Visualizing cross-validation behavior in scikit-learn](../../auto_examples/model_selection/plot_cv_indices.html#sphx-glr-auto-examples-model-selection-plot-cv-indices-py)
  - Parameters:
    - **n\_splits**int, default=5
    - Number of folds. Must be at least 2. Changed in version 0.22: `n_splits` default value changed from 3 to 5.
    - **shuffle**bool, default=False
    - Whether to shuffle the data before splitting into batches. Note that the samples within each split will not be shuffled.
    - **random\_state**int, RandomState instance or None, default=None
    - When `shuffle` is True, `random_state` affects the ordering of the
indices, which controls the randomness of each fold. Otherwise, this
parameter has no effect.
Pass an int for reproducible output across multiple function calls.
See [Glossary](../../glossary.html#term-random_state).
See also 
  - [`StratifiedKFold`](sklearn.model_selection.StratifiedKFold.html#sklearn.model_selection.StratifiedKFold)
  - Takes class information into account to avoid building folds with imbalanced class distributions (for binary or multiclass classification tasks).
  - [`GroupKFold`](sklearn.model_selection.GroupKFold.html#sklearn.model_selection.GroupKFold)
  - K-fold iterator variant with non-overlapping groups.
  - [`RepeatedKFold`](sklearn.model_selection.RepeatedKFold.html#sklearn.model_selection.RepeatedKFold)
  - Repeats K-Fold n times.
Notes The first `n_samples % n_splits` folds have size `n_samples // n_splits + 1`, other folds have size `n_samples // n_splits`, where `n_samples` is the number of samples.
Randomized CV splitters may return different results for each call of
split. You can make the results identical by setting `random_state` to an integer.
Examples \>>> import numpy as np >>> from sklearn.model\_selection import KFold >>> X = np.array(\[\[1, 2\], \[3, 4\], \[1, 2\], \[3, 4\]\]) >>> y = np.array(\[1, 2, 3, 4\]) >>> kf = KFold(n\_splits=2) >>> kf.get\_n\_splits() 2 >>> print(kf) KFold(n\_splits=2, random\_state=None, shuffle=False) >>> for i, (train\_index, test\_index) in enumerate(kf.split(X)): ... print(f"Fold {i}:") ... print(f" Train: index={train\_index}") ... print(f" Test: index={test\_index}") Fold 0: Train: index=\[2 3\] Test: index=\[0 1\] Fold 1: Train: index=\[0 1\] Test: index=\[2 3\] 
  - 
get\_metadata\_routing()[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/utils/_metadata_requests.py#L1743)[#](#sklearn.model_selection.KFold.get_metadata_routing)
  - Get metadata routing of this object. Please check [User Guide](../../metadata_routing.html#metadata-routing) on how the routing
mechanism works.
    - Returns:
      - **routing**MetadataRequest
      - A [`MetadataRequest`](sklearn.utils.metadata_routing.MetadataRequest.html#sklearn.utils.metadata_routing.MetadataRequest) encapsulating
routing information.
  - 
get\_n\_splits(*X=None*, *y=None*, *groups=None*)[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/model_selection/_split.py#L414)[#](#sklearn.model_selection.KFold.get_n_splits)
  - Returns the number of splitting iterations as set with the `n_splits` param
when instantiating the cross-validator.
    - Parameters:
      - **X**array-like of shape (n\_samples, n\_features), default=None
      - Always ignored, exists for API compatibility.
      - **y**array-like of shape (n\_samples,), default=None
      - Always ignored, exists for API compatibility.
      - **groups**array-like of shape (n\_samples,), default=None
      - Always ignored, exists for API compatibility.
    - Returns:
      - **n\_splits**int
      - Returns the number of splitting iterations in the cross-validator.
  - 
split(*X*, *y=None*, *groups=None*)[\[source\]](https://github.com/scikit-learn/scikit-learn/blob/afe5bcd80/sklearn/model_selection/_split.py#L62)[#](#sklearn.model_selection.KFold.split)
  - Generate indices to split data into training and test set. 
    - Parameters:
      - **X**array-like of shape (n\_samples, n\_features)
      - Training data, where `n_samples` is the number of samples
and `n_features` is the number of features.
      - **y**array-like of shape (n\_samples,), default=None
      - The target variable for supervised learning problems.
      - **groups**array-like of shape (n\_samples,), default=None
      - Always ignored, exists for API compatibility.
    - Yields:
      - **train**ndarray
      - The training set indices for that split.
      - **test**ndarray
      - The testing set indices for that split.

## Gallery examples[#](#gallery-examples)

[Feature agglomeration vs. univariate selection](../../auto_examples/cluster/plot_feature_agglomeration_vs_univariate_selection.html)

[Comparing Random Forests and Histogram Gradient Boosting models](../../auto_examples/ensemble/plot_forest_hist_grad_boosting_comparison.html)

[Categorical Feature Support in Gradient Boosting](../../auto_examples/ensemble/plot_gradient_boosting_categorical.html)

[Gradient Boosting Out-of-Bag estimates](../../auto_examples/ensemble/plot_gradient_boosting_oob.html)

[Visualizing cross-validation behavior in scikit-learn](../../auto_examples/model_selection/plot_cv_indices.html)

[Nested versus non-nested cross-validation](../../auto_examples/model_selection/plot_nested_cross_validation_iris.html)

[Target Encoder’s Internal Cross fitting](../../auto_examples/preprocessing/plot_target_encoder_cross_val.html)

[Release Highlights for scikit-learn 1.3](../../auto_examples/release_highlights/plot_release_highlights_1_3_0.html)