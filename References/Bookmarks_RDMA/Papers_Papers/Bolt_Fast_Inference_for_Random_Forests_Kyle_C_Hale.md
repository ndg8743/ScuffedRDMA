# Bolt: Fast Inference for Random Forests | Kyle C. Hale

- **Source:** https://www.halek.co/publication/romero-2022-bolt/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

Middleware '22

# Bolt: Fast Inference for Random Forests

*Proceedings of the 23rd ACM/IFIP International Middleware Conference*, October 2022.

## Abstract

Random forests use ensembles of decision trees to boost accuracy for machine learning tasks. However, large ensembles slow down inference on platforms that process each tree in an ensemble individually. We present Bolt, a platform that restructures whole random forests, not just individual trees, to speed up inference. Conceptually, Bolt maps every path in each tree to a lookup table which, if cache were large enough, would allow inference with just one memory access. When the size of the lookup table exceeds cache capacity, Bolt employs a novel combination of lossless compression, parameter selection, and bloom filters to shrink the table while preserving fast inference. We compared inference speed in Bolt to three state-of-the-art platforms: Python Scikit-Learn, Ranger, and Forest Packing. We evaluated these platforms using datasets with vision, natural language processing and categorical applications. We observed that on ensembles of shallow decision trees Bolt can run 2–14X faster than competing platforms and that Bolt's speedups persist as the number of decision trees in an ensemble increases.

## BibTeX

```
@inproceedings{ROMERO:2022:BOLT,
  author    = {Romero, Eduardo and Stewart, Christopher and Li, Angela and Hale, Kyle and Morris, Nathaniel},
  title     = {Bolt: Fast Inference for Random Forests},
  booktitle = {Proceedings of the 23rd ACM/IFIP International Middleware Conference},
  series    = {Middleware '22},
  year      = {2022},
  month     = {October},
  pages     = {94–106},
  numpages  = {13},
  publisher = {Association for Computing Machinery},
  address   = {New York, NY, USA},
  location  = {Quebec, QC, Canada},
  isbn      = {9781450393409},
  doi       = {10.1145/3528535.3531519},
  url       = {https://doi.org/10.1145/3528535.3531519}
}
```