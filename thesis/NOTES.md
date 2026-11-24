# Star notes in the thesis

Every note below is printed in the PDF with a star (*) in front of it. Nothing else in the PDF uses that character, so a search for * finds all of them. Page numbers are those printed on the pages of the last build (roman numbers are the front matter).

49 notes: 37 wait for a result or a record, 12 are things to fix, confirm or write.

## Waiting for results

- p. ii: Waiting for results from E3 and E8.
- p. 7: Waiting for results from E3 and E8: add the two headline numbers here.
- p. 46: Waiting for results from E1 to E5 on the verbs provider: state whether either difference occurs there.
- p. 86: Waiting for the hardware record of server 1 (run R0): board and processor.
- p. 88: Waiting for the hardware record of server 4 (run R0): state which of the two changes is active, and confirm that the board starts with both V100 cards installed.
- p. 94: Waiting for the same check across the lab pair (with E8).
- p. 101: Waiting for results from the quantizer on long prompts (run R4). (placeholder figure: Quantizer on long prompts with real queries)
- p. 104: Waiting for results from the storage sweep on the NVMe drive with repeats (run R3). (placeholder figure: Storage tier sweep on the NVMe drive with repeats)
- p. 105: Waiting for results from the link baselines (run R1).
- p. 106: Waiting for results from the link baseline of the lab pair (run R1). (placeholder figure: Link baseline of the lab pair on the direct 10GbE cable)
- p. 106: Waiting for results from the link baseline of the home pair (run R1). (placeholder figure: Link baseline of the home pair between two machines)
- p. 107: Waiting for results from E1 (run R2).
- p. 107: Waiting for results from E1 on both pairs (run R2). (placeholder figure: E1: Latency against message size for each stack)
- p. 108: Waiting for results from E2 (run R2).
- p. 108: Waiting for results from E2 on both pairs (run R2). (placeholder figure: E2: Bandwidth of bulk writes against write size)
- p. 109: Waiting for results from E3 (run R2).
- p. 109: Waiting for results from E3 on both pairs (run R2). (placeholder figure: E3: Penalty on the hot tail latency with one and two endpoints)
- p. 110: Waiting for results from E4 (run R2).
- p. 110: Waiting for results from E4 on both pairs (run R2). (placeholder figure: E4: Hot tail latency under load for six libfabric configurations)
- p. 111: Waiting for results from E5 (run R2).
- p. 111: Waiting for results from E5 on both pairs (run R2). (placeholder figure: E5: Latency and instructions per operation for five completion signals)
- p. 112: Waiting for results from E6 (run R5).
- p. 112: Waiting for results from E6 (run R5), after the stall of blobs larger than one slot is fixed. (placeholder figure: E6: Time to move one blob over the blob channel and over TCP)
- p. 113: Waiting for results from E7 (run R6).
- p. 113: Waiting for results from E7 (run R6). (placeholder figure: E7: Split serving on a single GPU against a single instance)
- p. 114: Waiting for results from E8 (run R7).
- p. 114: Waiting for results from E8 (run R7).
- p. 115: Waiting for results from E8 (run R7). (placeholder figure: E8: Time to first token against prompt length for five setups)
- p. 115: Waiting for results from E3.
- p. 116: Waiting for results from E3 and E8: this subsection is written from them.
- p. 116: Waiting for results from E3 and E8. (placeholder figure: Share of the transfer in the time to first token, by setup)
- p. 121: Waiting for results from E3 and E8: add one sentence that places the measured result among these systems.
- p. 122: Waiting for results from E3 and E4: state the answer for each stack in one sentence and fill the blanks.
- p. 122: Waiting for results from E1, E2 and E5: state the answer in one sentence and fill the blanks.
- p. 123: Waiting for results from E8: state the answer to the first half and fill the blanks.
- p. 125: Waiting for results from E3 and E8: fill the blanks, and keep the opening sentence of this paragraph only if they support it.
- p. 125: Waiting for results from E3: close with what the software network card allowed.

## To fix, confirm or write

- approval page: fill in [Name]
- approval page: fill in [Department]
- p. iii: To be written.
- p. 43: Confirm against the connector at the commit used for the runs: the two statements above, the single send queue of the sender, and the marker that the decode side does not wait for ([sec:connector]). If the decision components are connected to the serving path first, rewrite this paragraph and the dashed box of [fig:architecture].
- p. 50: Fix before E6: blobs larger than one slot stall intermittently when the channel runs on the TCP provider of libfabric in loopback (reproducer: `benchmarks/fabric/blob_multichunk_check.py`; cause not identified). With 4 MiB slots a layer of Granite 3.3 2B fits in one chunk for prompts up to about 2,000 tokens, so the 2,048-token and 4,096-token points of E8 need the fix or a larger slot. If the stall is still open at submission, state it here as a limitation.
- p. 70: Decide before submission: apply one of the two repairs in the code and measure it (run R8), or keep this section as the analysis of the rule as implemented.
- p. 93: Fix in the repository: restore the MIT notice of libmesh-rdma in the three ported files.
- p. 100: Fix in the repository: `benchmark_scuffed_quant_llm.py` divides the 16-bit size by the ratio against 32-bit, so the field `kv_compressed_bytes` of `scuffed_quant_llm.json` is half the true value. The sizes in [tab:quant] are computed from the packed format.
- p. 102: Fix in the repository: the files behind the last row are named `mamba3` and carry that architecture label, although the model that ran was `state-spaces/mamba-130m-hf`.
- p. 103: The sweep above wrote to a temporary directory and did not record the drive or the file system, so it is not certain that the writes reached the NVMe drive. Run R3 replaces it; remove this note with the old figure.
- p. 104: Rerun at the current commit and replace this table: these values were taken before the benchmark checked the status of every completion ([sec:rules]).
- p. 143: This section lists the outstanding runs: remove it, or reduce it to the commands of each run, when they are complete. R0 to R4 need no change to the code. If R5 is not completed, the evaluation rests on E1 to E5 with R3 and R4 and on the shorter prompts of E8.
