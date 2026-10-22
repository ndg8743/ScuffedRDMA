# Automated Machine Learning (AutoML)  |  Google for Developers

- **Source:** https://developers.google.com/machine-learning/crash-course/automl
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

## Page Summary

- AutoML automates tasks in the machine learning workflow, like feature engineering, algorithm selection, and hyperparameter tuning, making model building faster and easier.
- While manual training involves writing code and iteratively adjusting it, AutoML reduces repetitive work and the need for specialized skills.
- AutoML empowers users to focus on the core machine learning problem and data instead of getting bogged down in manual tasks within the model development cycle.
- This module explores the benefits and limitations of using AutoML, common patterns, and how to apply them to machine learning projects, assuming prior knowledge of basic machine learning concepts.

If you are starting a new machine learning (ML) project, you may be wondering if manual training is your only option to build a machine learning model. With manual training, you write code using an ML framework to create a model. During this process, you choose which algorithms to explore and iteratively tune hyperparameters to find the right model.

Of course, model training is not the only thing you need to think about. In practice, building a machine learning model from prototype to production involves repetitive tasks and specialized skills. A simple exploratory ML workflow looks something like this:

**Repetitive tasks** - The ML workflow can involve repetitive work and
experimentation. For example, during model development you typically need to
explore different combinations of algorithms and hyperparameters to identify the
most appropriate model. With manual training, you write specialized code to
train the model and then adjust the code to run experiments with different ML
algorithms and hyperparameters to find the best model. For small or exploratory
projects this manual process may not be a problem, but for larger projects these
repetitive tasks can be time consuming.

**Specialized Skills** - Manually developing an ML model involves specialized
skills. In practice, not every team planning to develop a machine learning model
may have these skills. If a team does not have a dedicated data scientist, doing
this work manually might not even be feasible.

Luckily, certain steps in model development can be automated to reduce the burden of repetitive work and the need for specialized skills. Automating these tasks is the subject of this module on automated machine learning (AutoML).

## What is AutoML?

[**AutoML**](/machine-learning/glossary#automl) is a process of automating
certain tasks in a machine learning workflow.
You can think of AutoML as a set of tools and technologies that make building
machine learning models faster and more accessible to a wider group of users.
Though automation can help throughout the ML workflow, the tasks that are often
associated with AutoML are the ones included in the model development cycle
shown in Figure 1. These repetitive tasks include:

- **Data Engineering**
  - Feature engineering.
  - Feature selection.
- **Training**
  - Identifying an appropriate ML algorithm.
  - Selecting the best hyperparameters.
- **Analysis**
  - Evaluating metrics generated during training based on test and validation datasets.

With AutoML, you can focus on your ML problem and data rather than on feature selection, tuning hyperparameters, and choosing the right algorithm.