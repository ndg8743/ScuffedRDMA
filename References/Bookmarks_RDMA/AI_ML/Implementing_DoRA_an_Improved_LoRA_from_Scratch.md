# Implementing DoRA (an Improved LoRA) from Scratch

- **Source:** https://www.dailydoseofds.com/implementing-dora-an-improved-lora-from-scratch/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Implementing DoRA (an Improved LoRA) from Scratch

A powerful LoRA-variant explained in a beginner-friendly way and implemented in PyTorch.

## Introduction

We have covered several LLM fine-tuning approaches before, which are also illustrated in this visual:

We covered them below:

**Weight-decomposed low-rank adaptation (DoRA)** is yet another promising and among the state-of-the-art technique that improves LoRA and other similar fine-tuning techniques.

The following chart, taken from the research paper, depicts that DoRA achieves much better performance compared to LoRA at similar rank values (`r`).

If you don't understand what rank (`r`) is or what exactly LoRA is, don't worry.

Let's quickly recap LLM fine-tuning, the challenges, and how LoRA helps, along with an implementation.

Once that's done, we shall break down DoRA, understand how it improves LoRA, and implement it from scratch using PyTorch.

Let's begin!

## Recap

In the pre-LLM era, whenever someone open-sourced any high-utility model for public use, in most cases, practitioners would fine-tune that model to their specific task.

[As also discussed in the most recent article on vector databases](https://www.dailydoseofds.com/a-beginner-friendly-and-comprehensive-deep-dive-on-vector-databases/), fine-tuning means adjusting the weights of a **pre-trained model** on a new dataset for better performance. This is depicted in the animation below:

The motivation to do this is pretty simple.

When the model was developed, it was trained on a specific dataset that might not perfectly match the characteristics of the data a practitioner wants to use it on.

The original dataset might have had slightly different distributions, patterns, or levels of noise compared to the new dataset.

Fine-tuning allows the model to adapt to these differences, learning from the new data and adjusting its parameters to improve its performance on the specific task at hand.

For instance, consider **BERT**. It’s a Transformer-based language model, which is popularly used for text-to-embedding generation (**92k+ citations on the original paper**).

It’s open-source.

[As we discussed in the vector database deep dive](https://www.dailydoseofds.com/a-beginner-friendly-and-comprehensive-deep-dive-on-vector-databases/), BERT was pre-trained on a large corpus of text data, which might be very very different from what someone else may want to use it on.

Thus, when using it on any downstream task, we can adjust the weights of the BERT model along with the augmented layers, so that it better aligns with the nuances and specificities of the new dataset.

The idea makes total practical sense. In fact, it has been successfully used for a long time now, not just after the release of BERT but even prior to that.

However, the primary reason why fine-tuning has been pretty successful in the past is that we had not been training models that were ridiculously massive.

Talking of BERT again, it has two variants:

1. BERT-Base, which has 110M parameters (or .11B).
2. BERT-Large, which has 340M parameters (or .34B).

This size isn’t overwhelmingly large, which makes it quite feasible to fine-tune it on a variety of datasets without requiring immense computational resources.

### Issues with fine-tuning

However, a problem arises when we use the same traditional fine-tuning technique on much larger models — LLMs, for instance.

This is because, as you may already know, these models are huge — billions or even trillions of parameters.

Consider **GPT-3**, for instance. It has 175B parameters, which is 510 times bigger than even the larger version of BERT called **BERT-Large**:

And to give you more perspective, I have successfully fine-tuned BERT-large in many of my projects on a single GPU cluster, like in [this paper](https://arxiv.org/pdf/2111.15436.pdf?ref=dailydoseofds.com) and [this paper](https://ieeexplore.ieee.org/abstract/document/9627061/?ref=dailydoseofds.com).

But it would have been impossible to do the same with GPT-3.

Moving on, while OpenAI has not revealed the exact number of parameters in GPT-4, it is suspected to be around 1.7 Trillion, which is roughly ten times bigger than GPT-3:

Traditional fine-tuning is just not practically feasible here, and in fact, not everyone can afford to do it due to a lack of massive infrastructure.

### Business perspective

In fact, it’s not just about the availability of high computing power.

Consider this...

OpenAI trained GPT-3 and GPT-4 models in-house on massive GPU clusters, so they have access to them for sure.

However, they also provide a [fine-tuning API](https://platform.openai.com/docs/guides/fine-tuning?ref=dailydoseofds.com) to customize these models according to our application, which is currently available for the following models: `gpt-3.5-turbo-1106`, `gpt-3.5-turbo-0613`, `babbage-002`, `davinci-002`, and `gpt-4-0613`:

Going by traditional fine-tuning, for every customer wanting to have a customized version of any of these models, OpenAI would have to dedicate an entire GPU server to load it and also ensure that they maintain sufficient computing capabilities for fine-tuning requests.

Deploying such independent instances of fine-tuned models, each with 175B parameters, is prohibitively expensive.

To put it into perspective, a GPT-3 model checkpoint is estimated to consume about 350GBs. And this is the static memory of the model, which only includes model weights. It does not even consider the memory required during training, computing activations, running backpropagation, and more.

And to make things worse, what we discussed above is just for one customer, but they already have thousands of customers who create a customized version of OpenAI models that is fine-tuned to their dataset.

In fact, there are many other users who just want to explore the fine-tuning capabilities (for skill development or general exploration, maybe), but they may never want to use that model to serve any end-users.