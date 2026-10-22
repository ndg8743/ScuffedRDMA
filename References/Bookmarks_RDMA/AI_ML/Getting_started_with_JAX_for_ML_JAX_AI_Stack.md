# Getting started with JAX for ML — JAX AI Stack

- **Source:** https://docs.jaxstack.ai/en/latest/getting_started.html
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Getting started with JAX for ML[#](#getting-started-with-jax-for-ml)

[JAX](http://jax.readthedocs.io) is a Python package for accelerator-oriented array computation and program transformation, and is the engine behind cutting-edge AI research and production models at Google and beyond.

## Who is this tutorial for?[#](#who-is-this-tutorial-for)

This tutorial is for those who want to get started using JAX and JAX-based AI libraries - the JAX AI stack - to build and train a simple neural network model. [JAX](http://jax.readthedocs.io) is a Python library for hardware accelerator-oriented array computation and program transformation, and is the engine behind cutting-edge AI research and production models at Google, Google DeepMind, and beyond. This tutorial assumes some familiarity with numerical computing in Python with [NumPy](http://numpy.org), and assumes some conceptual familiarity with defining, training, and evaluating machine learning models.

## What does this tutorial cover?[#](#what-does-this-tutorial-cover)

JAX focuses on [array-based](https://jax.readthedocs.io/en/latest/key-concepts.html#jax-arrays-jax-array) computation, and is at the core of a growing ecosystem of domain-specific tools. This tutorial introduces part of that JAX ecosystem designed for AI-related tasks, including:

- [Flax NNX](http://flax.readthedocs.io): A machine learning library designed for defining and building scalable neural networks using JAX.
- [Optax](http://optax.readthedocs.io): A high-performance function optimization library that comes with built-in optimizers and loss functions.

After working through this content, you may wish to visit the [JAX documentation site](http://jax.readthedocs.io/) for a deeper dive into the core JAX concepts.