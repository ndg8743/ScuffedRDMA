# Pinecone claims up to 97% lower costs with dedicated read nodes

- **Source:** https://www.blocksandfiles.com/ai-ml/2026/04/15/pinecone-claims-up-to-97-lower-costs-with-dedicated-read-nodes/5217712
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

AI/ML

# Pinecone claims up to 97% lower costs with dedicated read nodes

Vector database supplier Pinecone is supplying dedicated read nodes (DRN) to cut charges by up to 97 percent versus its standard on-demand pricing scheme.

The DRN concept has been in public preview since December and is now generally available. Pinecone says it is worthwhile when a customer's workload has:

- Consistent or high QPS (queries per sec): Hourly per-node pricing beats per-request pricing, often significantly
- Large vector counts: Hundreds of millions to billions of vectors benefit from DRN's always-hot data path, with indexes kept in memory and on local SSD, so there are no cold start latency regressions
- Tight latency SLOs: Dedicated resources give you a performance floor you control
- Predictable spend requirements: Fixed hourly pricing makes forecasting straightforward

In contrast, on-demand is the right fit for:

- Bursty or variable workloads: Elastic scaling and per-request pricing are more efficient
- Dev/test environments and prototypes: Lower cost, zero provisioning
- Workloads with many small namespaces: on-demand's low latency and effortless scaling shine here

It has produced three customer cases where DRN use produced large savings:

Note that p50 is the 50th percentile latency, meaning, for example, that 50 percent of all queries complete in 31 milliseconds or less. The p99 term refers to the 99th percentile latency (often called tail latency), meaning that 99 percent of all queries complete in 39 milliseconds or less.

A major music licensing marketplace runs semantic search over a catalog of 1 billion vectors in a single namespace. Query volume is low at about 8 QPS, but the dataset is large enough that per-request pricing adds up fast, because every query scans a massive index.

On DRN, this workload runs on T1 nodes with 14 shards and one read replica. Latency is tight: 31 ms p50, 39 ms p99. This workload costs 77 percent less to run on DRN.

A global enterprise networking company uses Pinecone for search across a 6.1 million vector index at 20-50 QPS. The workload is small in vector count but latency-sensitive, and the consistent query volume makes per-request pricing expensive relative to the dataset size.

On DRN, this workload runs on T1 nodes with two shards and two read replicas. It achieves 12 ms p50 and 45 ms p99. This workload costs 83 percent less to run on DRN.

A major academic and scientific publishing platform runs sustained search traffic at 200-270 QPS across a 14 million vector index. This is the workload profile where per-request pricing diverges most sharply from provisioned pricing: moderate-to-large dataset, high and consistent query volume.

On DRN, this workload runs on T1 nodes with 1 shard and 4 read replicas. They hit 45ms p50 and 91ms p99. This workload costs 97 percent less to run on DRN.

DRN gives a vector index a dedicated serving layer for reads while leaving everything else unchanged: the same Pinecone APIs and SDKs, same write pipeline, and the same operational model for the index lifecycle.

Customers get dedicated, provisioned read capacity per index; a warm data path with data kept in memory and on local SSD; and no read rate limits. Dedicated resources mean they control their throughput ceiling.

Read more about Pinecone DRN's new GA capabilities [here](https://www.pinecone.io/blog/dedicated-read-nodes-ga-features/).