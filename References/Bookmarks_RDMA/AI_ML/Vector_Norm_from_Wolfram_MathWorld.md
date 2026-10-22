# Vector Norm -- from Wolfram MathWorld

- **Source:** https://mathworld.wolfram.com/VectorNorm.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

Given an -dimensional
 [vector](/Vector.html)

|  | (1) | 

a general vector norm ,
 sometimes written with a [double bar](/DoubleBar.html) as , is a [nonnegative](/Nonnegative.html) [norm](/Norm.html)
 defined such that

1\.  when  and  [iff](/Iff.html) .

2\.  for any [scalar](/Scalar.html) .

3\. .

In this work, a [single bar](/SingleBar.html) is used to denote a vector norm, [absolute value](/AbsoluteValue.html), or [complex
 modulus](/ComplexModulus.html), while a [double bar](/DoubleBar.html) is reserved for denoting
 a [matrix norm](/MatrixNorm.html).

The vector norm for , 2, ... is defined as

|  | (2) | 

The -norm of vector  is implemented as `[Norm](http://reference.wolfram.com/language/ref/Norm.html)`\[*v*,
 *p*\], with the 2-norm being returned by `Norm`\[*v*\].

The special case is defined as

|  | (3) | 

The most commonly encountered vector norm (often simply called "the norm" of a vector, or sometimes the magnitude of a vector) is the [*L*<sup>2</sup>-norm](/L2-Norm.html),
 given by

|  | (4) | 

This and other types of vector norms are summarized in the following table, together with the value of the norm for the example vector .

| name | symbol | value | approx. | 
| -norm |  | 6 | 6.000 | 
| -norm |  |  | 3.742 | 
| -norm |  |  | 3.302 | 
| -norm |  |  | 3.146 | 
| -norm |  | 3 | 3.000 |