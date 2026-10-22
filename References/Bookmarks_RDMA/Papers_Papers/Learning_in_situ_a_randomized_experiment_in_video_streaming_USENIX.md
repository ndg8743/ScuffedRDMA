# Learning in situ: a randomized experiment in video streaming | USENIX

- **Source:** https://www.usenix.org/conference/nsdi20/presentation/yan
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > Papers > Papers)
- **Retrieved:** 2026-10-22


---

Francis Y. Yan and Hudson Ayers, *Stanford University;* Chenzhi Zhu, *Tsinghua University;* Sadjad Fouladi, James Hong, Keyi Zhang, Philip Levis, and Keith Winstein, *Stanford University*

***Community Award Winner!***

We describe the results of a randomized controlled trial of video-streaming algorithms for bitrate selection and network prediction. Over the last year, we have streamed 38.6 years of video to 63,508 users across the Internet. Sessions are randomized in blinded fashion among algorithms.

We found that in this real-world setting, it is difficult for sophisticated or machine-learned control schemes to outperform a "simple" scheme (buffer-based control), notwithstanding good performance in network emulators or simulators. We performed a statistical analysis and found that the heavy-tailed nature of network and user behavior, as well as the challenges of emulating diverse Internet paths during training, present obstacles for learned algorithms in this setting.

We then developed an ABR algorithm that robustly outperformed other schemes, by leveraging data from its deployment and limiting the scope of machine learning only to making predictions that can be checked soon after. The system uses supervised learning *in situ*, with data from the real deployment environment, to train a probabilistic predictor of upcoming chunk transmission times. This module then informs a classical control policy (model predictive control).

To support further investigation, we are publishing an archive of data and results each week, and will open our ongoing study to the community. We welcome other researchers to use this platform to develop and validate new algorithms for bitrate selection, network prediction, and congestion control.

NSDI '20 Open Access Sponsored by NetApp

## Open Access Media

USENIX is committed to Open Access to the research presented at our events. Papers and proceedings are freely available to everyone once the event begins. Any video, audio, and/or slides that are posted after the event are also free and open to everyone. [Support USENIX](/annual-fund) and our commitment to Open Access.

author = {Francis Y. Yan and Hudson Ayers and Chenzhi Zhu and Sadjad Fouladi and James Hong and Keyi Zhang and Philip Levis and Keith Winstein},

title = {Learning in situ: a randomized experiment in video streaming },

booktitle = {17th USENIX Symposium on Networked Systems Design and Implementation (NSDI 20)},

year = {2020},

isbn = {978-1-939133-13-7},

address = {Santa Clara, CA},

pages = {495--511},

url = {https://www.usenix.org/conference/nsdi20/presentation/yan},

publisher = {USENIX Association},

month = feb

}