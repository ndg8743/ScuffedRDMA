# How To Build and Use a Multi GPU System for Deep Learning — Tim Dettmers

- **Source:** https://timdettmers.com/2014/09/21/how-to-build-and-use-a-multi-gpu-system-for-deep-learning/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

When I started using GPUs for deep learning my deep learning skills improved quickly. When you can run experiments of algorithms and algorithms with different parameters and gain rapid feedback you can just learn much more quickly. At the beginning, deep learning is a lot of trial and error: You have to get a feel what parameters need to be adjusted, or what puzzle piece is missing in order to get a good result. A GPU helps you to fail quickly and learn important lessons so that you can keep improving. Soon my deep learning skills were sufficient to take the [2<sup>nd</sup> place in the Crowdflower competition](https://www.kaggle.com/c/crowdflower-weather-twitter/discussion/6488#35640) where the task was to predict weather labels from given tweets (sunny, raining etc.).

After this success I was tempted to use multiple GPUs in order to train deep learning algorithms even faster. I also took interest in learning very large models which do not fit into a single GPU. I thus wanted to build a little GPU cluster and explore the possibilities to speed up deep learning with multiple nodes with multiple GPUs. At the same time I was offered to do contract work as a data base developer through my old employer. This gave me opportunity to get the money to build the GPU cluster I thought of.

**Important components in a GPU cluster**

When I did my research on which hardware to buy I soon realized, that the main bottleneck will be the network bandwidth, i.e. how much data can be transferred from computer to computer per second. The network bandwidth of network cards (affordable cards are at about 4GB/s) does not come even close to the speed of PCIe 3.0 bandwidth (15.75 GB/s). So GPU-to-GPU communication within a computer will be fast, but it will be slow between computers. On top of that most network card only work with memory that is registered with the CPU and so the GPU to GPU transfer between two nodes would be like this: GPU 1 to CPU 1 to Network Card 1 to Network Card 2 to CPU 2 to GPU 2. What this means is, if one chooses a slow network card then there might be no speedups over a single computer. Even with fast network cards, if the cluster is large, one does not even get speedups from GPUs when compared to CPUs as the GPUs just work too fast for the network cards to keep up with them.

This is the reason why many big companies like Google and Microsoft are using CPU rather than GPU clusters to train their big neural networks. Luckily, Mellanox and Nvidia recently came together to work on that problem and the result is GPUDirect RDMA, a network card driver that can make sense of GPU memory addresses and thus can transfer data directly from GPU to GPU between computers.

Generally your best bet for cheap network cards is eBay. I won an auction for a set of 40Gbit/s Mellanox network cards that support GPUDirect RDMA along with the fitting fibre cable on eBay. I already had two GTX Titan GPUs with 6GB of memory and as I wanted to build huge models that do not fit into a single memory, so I decided to keep the 6GB cards and buy more of them to build a cluster that features 24GB memory. In retrospect this was a rather foolish (and expensive) idea, but little did I know about the performance of such large models and how to evaluate the performance of GPUs. All the lessons I learned from this can be found [here](https://timdettmers.com/2020/09/07/which-gpu-for-deep-learning/). Besides that the hardware is rather straightforward. For fast inter-node communication PCIe 3.0 is faster than PCIe 2.0, so I got a PCIe 3.0 board. It is also a good idea to have about two times the RAM than you have GPU memory to be able to work more freely to handle big nets. As deep learning programs use a single thread for a GPU most of the time, a CPU with as many cores as GPUs you have is often sufficient.

**Hardware: Check. Software: ?**

There are basically two options how to do multi-GPU programming. You do it in CUDA and have a single thread and manage the GPUs directly by setting the current device and by declaring and assigning a dedicated memory-stream to each GPU, or the other options is to use [CUDA-aware MPI](https://developer.nvidia.com/blog/introduction-cuda-aware-mpi/) where a single thread is spawned for each GPU and all communication and synchronization is handled by MPI. The first method is rather complicated as you need to create efficient abstractions where you loop through the GPUs and handle streaming and computing. Even with efficient abstractions your code can blow up quickly in line count making it less readable and maintainable.

The second option is much more efficient and clean. MPI is the standard in high performance computing and its standardized library means that you can be sure that a MPI method really does what it is supposed to do. Underlying MPI the same principles are used as in the first method describes above, but the abstraction is so good that it is quite easy to adapt single GPU code to multiple GPU code (at least for data parallelism). The result is clean and maintainable code and as such I would always recommend using MPI for multi-GPU computing. As MPI libraries come in many languages and you can pair them with the language of your choice. With these two components you are ready to go and can immediately start programming deep learning algorithms for multiple GPUs.

\[Image source:  [NVIDIA GPUDirect Key Technologie](https://developer.nvidia.com/gpudirect)s\]

Sunil says

Hi Tim,

Thanks for your excellent articles, really helpful and great expertise.

I’m working on DL for medical signal processing and currently just using a GTX1070 which is slowing me down significantly. I’m looking at buying 2 RTX 3080s to run in parallel on a single machine. Do I need anything (like NVLink) to connect them or can they just go straight onto the motherboard and let the software (Tensorflow) do the parallelisation? Secondly, my motherboard specs say it can run a x16 bandwidth in the first PCIe slot but “x8 or above is not recommended for VGA cards” for the other slots even though they are called “x16” slots (it’s a 28-lane CPU). Does this matter? Will it slow everything down if parallelised (i.e. will both cards need to work at x4 or x8?) orwill it be impossible to parallelise?

Thanks in advance for your help!

Tim Dettmers says

Hi Sunil,

everything should be alright in your case: No NVLink needed, and 8x lanes are fine for 2 GPUs – it should not be much slower (maybe 1-5%).

Deterministic says

Hello Tim,

Congrats for your excellent articles! I would like your advice on a setup for deep learning with images.

I have 2 PCs currently with GTX 1060 and thought to replace those for 2x 2080 Ti in each PC and make a cluster with them (potentially adding more later), also will connect the GPUs with a fast direct link like you did if it’s worth it.

Some questions arise though, is the Titan RTX a safer bet for the extra memory? Not sure the Titan takes the same space and slots as the 2080… Also, NVlink between pairs of 2080 would double the memory I think, although I don’t know if it will work out of the box or needs specific libraries. What do you think?

Thanks!

Tim Dettmers says

I would use the two systems separately and do not connect them with each other (not worth it, a good interconnect is expensive has little benefit). The Titan RTX fit in the same slot as RTX 2080 but two of them next to each other overheat quickly — so maybe stick with the RTX 2080. You do not need NVLink for 2 GPUs the normal transfer via PCIe is more than enough.

Alam Noor says

Hi Tim,

I have two GPUs Machines one is 2080 TI and GeForce RTX 2070. Now I want to use both GPUs for training at object detection big data. Can you please comment, how I can configure for one task. Please comment step by step, I will be thankful to have your valuable comments and time. Thanks

Tim Dettmers says

This setup is too difficult or even impossible to use for a single task. What you can do is to run two separate tasks on each of these machines.

fusedentropy says

Something not mentioned is that, on Windows OS systems, GpuDirect only works when the GPU in TCC-Mode. If you are going GPU-to-GPU, both GPUs need to be in TCC-Mode. This is also true for P2P.

NVIDIA insists that it is a limitation with Windows’ WDDM Mode architecture. Frankly, I don’t believe them. All that is needed for DMA is the physical memory address of both the src and dst. The NVIDIA driver can easily get this value.

At that point, what the GPU does is a don’t care for the Windows OS. The GPU has so many schedulers, I am sure it could schedule a DMA of the memory, usually some multiple of a page size.

I am sure industry would love to be able to do DMA from their compute (TCC) GPUs to their display (WDDM) GPU after all their CUDA kernels have finished crunching the data. Then use OpenGL Interop for display/rendering – all data stays on GPUs!! Never having to double-copy to host memory (GPU memory throughput is also much faster). Now add NVLINK and you avoid PCIe traffic between GPUs as well!! AWESOME!

NVIDIA insists this is not possible due to Windows (WDDM) – Really?

Tim Dettmers says

I am not familiar with the details on Windows, but from my personal experience, a lot of things are documented as “not working” under certain conditions when they actually are. This might be to make people buy cards that “support features” such as Tesla, or potentially, in this case, to save NVIDIA from troubles that are difficult to anticipate: Few users work this such systems in that way, so its difficult to support them, so they want to save troubles with support requests by just saying it does not work — period. I think this might be going on here.

fusedentropy says

Thank you for the reply.

I have the same suspicion – It must be possible, but for some reason, not supported at this time. Also, NVIDIA does not seem to want to entertain the idea.

I do know that the NVIDIA driver does “disable” the capabilities. One example is failure to “enable Peer access” – cudaDeviceEnablePeerAccess .

I’ve been looking for a hack to get around the limitation. I even though about using some daemon, running on Ubuntu which would be running inside a Hyper-V on top of the Win10. I would use some sort of event or interrupt to trigger the daemon to perform a deviceToDevice memcpy. Unfortunately, I have read that the NVIDIA drivers will not work with the Ubuntu system in this scenario.

At any rate, gotta keep on trekking in spite of the bumps in the road; this is part of what engineers do.

Cheers!

minecraft says

It’s going to be ending of mine day, however before finish I

am reading this enormous piece of writing to improve my experience.

Rock says

Hi folks, I wish to integrate a single system with four Quadro P6000 graphics cards connected through SLI link. Would ther make the GPGPU appear as a single large GPGPU or would it keep each of the GPGPU appear discrete to my application.

Would this implementation increase my performance over having four different host computers each with a single GPGPU?

Tim Dettmers says

SLI will not work for compute, it is for gaming only. You need to use data parallelization algorithms if you want to achieve the same effect. Many frameworks, including PyTorch supports this feature.

dataengine1@gmail.com says

Hi Tim,

Excellent Blog! I am considering experimenting with re-purposing an altcoin mining rig for Machine Learning and wanted to know what would be required and how it would compare to, for example, an expensive Tesla P100 system.

Concept would be to use one of my rigs and perhaps add hardware as needed to optimize for ML.

Current specs on Rig:

PRIME Z270-A, Intel Z270 Chipset, LGA 1151, HDMI, ATX Motherboard

Core i3-7100 Dual-Core 3.9GHz, LGA 1151, 51W TDP, Retail Processor

8GB HyperX Fury DDR4 2400MHz, CL15, Black, DIMM Memory

8 x GeForce GTX 1080 Ti DUKE 11G OC, 1531 – 1645MHz, 11GB GDDR5X, Graphics Card

1TB BarraCuda ST1000DM010, 7200 RPM, SATA 6Gb/s NCQ, 64MB cache

Are there features of this rig that are holding it back from ML performance?

Should additional hardware be added or replaced to easily convert?

Could I also parallel multiple rigs to form a large ML cluster?

Thank you for your feedback!

Tim Dettmers says

This rid looks like a perfect rig for ML. For some tasks, the RAM might be a bit low though, 16GB of RAM might be more comfortable to work with. With this system, you will probably not be able to parallelize all GPUs, but you should be fine to use them in for a neural network each. For efficient parallelization, you can try to remove 4 GPUs to free up some PCIe lanes. If that does not work well you will need to get a new motherboard and CPU and split your GPUs up into two systems with 4 GPUs each.

Khong Che says

Having read this I believed it was really informative. I appreciate

you spending some time and effort to put this information together.

I once again find myself personally spending a lot of time both reading and leaving comments.

But so what, it was still worthwhile!

Tim Dettmers says

Thank you, I really appreciate your comment! Comments like this keep me going with my blog 😉

Koustubh says

Great article. Can you please tell me if I plan to have 2 1080 ti gpus in single computer, will I have to do something to enable p2p access between them? I am little confused because there are other articles saying p2p is only for tesla and quadro gpus.

Sarkar says

Dear Tim,

Very insightful and helpful article; for serious deep learning experiments, how does one compare using 2×1050 (6GB) connected via SLI bridge using 2xPCIe 3.0 slot operating at x8, as opposed to a single 1080 Ti (11GB) using a PCIe 3 slot operating at x16?

Will the performance be same? What would be the limit of such a configuration in terms of deep learning workloads that can be efficiently handled?

Needless to say, 2×1080 Ti is better, but that is a much more expensive too.

Best regards,

Ravi Teja says

Hi Tim, thanks for the article.I have a question regarding using multiple gpus which are different models in one node. For ex: if I want to use a 1080/1070 and 1080 ti to train by data parellelism, what could be the bottlenecks ? would 1080 ti get bottlenecked by other gpu ?

Thank You

Tim Dettmers says

Unfortunately, parallelism is not support between GPUs which use a different chipset, for example, a GTX 1070 and GTX 1080 cannot communicate with each other directly. So this would not work out in the first place.

Ravi Teja says

Thank you Tim, for your reply.But, this thread says that tensorflow supports multi-gpu of different of types. https://github.com/tensorflow/tensorflow/issues/4013

a.zoragh says

hi

i am phd candidate and my thesis is about implementation of a frequent itemset mining or DNN algorithms on more than one GPU on a single node.my master(teacher)very strongly

ask me why you think this subject can be a phd thesis.if i can find a algorithm or a model that for running or implementation need more than one GPU i could give response to my master.is it possible you help me for this?what is your sugest?many thanks from your future resonse.

Tim Dettmers says

This subject could be a PhD thesis but it is difficult and you want to work with at least a small GPU cluster with 10+ computers or +32 GPUs to be relevant. Such a cluster must have the right interconnects (FDR Infiniband or better) to be relevant. Note that working in paralellism is very difficult engineering work with little payoff. I moved away from parallelism because it was not worth it when I looked at work required / payoff. People think this work is important, but there are only very few people how are interested in this and with whom you can discuss work so that it can be a very isolating experience especially at conferences.

If you want to do this despite all of this I recommend you to study block momentum and 1-bit gradient descent. These are by far the best methods our there. You should also study Google’s algorithm and understand that they have no future since they are very inefficient. You should understand why any further research on 1-bit-gradient-descent-like methods is a deadend (one can use methods like this on top of it, but it does not get better from there).

The real research is improving on block momentum. However, this is not straightforward and block momentum has poor theoretical motivations. It is an algorithm that should not work and yet it is the best parallel algorithm for deep learning. Your PhD could revolve around why this is and how to improve with these insights.

Again this is a difficult topic which requires lots of engineering. It will be easy to publish, but you will not be cited much and it will be difficult to build an academic career on this work. If you want to continue this work in industry though you will be an extremely valuable asset and should be easily getting jobs at companies that do deep learning on GPU clusters. If you are interested in deep learning in general though it will be very difficult to find a job for that. In your work you would speed up other peopls algorithms, but would not use them yourself in experiments other than benchmarking.

Hope that helps to set some expectations. If you have more questions, feel free to write me an email.

grant says

Is there still no “clean” solution to using AI, ML, and DL on multiple GPU?

Tim Dettmers says

Unfortunately not. PyTorch has made good efforts recently to do better, but I would still say that their solution is not really clean. Kind of disheartening to see no good solution to this problem for such a long time. I tried building automatic multi-GPU libraries myself, but it is just to much work to do as a single individual.

Adarsh says

Hello Tim, For video analytics, can we use GPU Direct for transferring Frames from capture card to GPU memory, after which frames will be inferred by a deep learning model ?

Tim Dettmers says

That depends if the other device supports GPU Direct (which it probably does not). If it does not support GPU Direct out-of-the-box, one might be able to get it working with some hacks to the drivers since both systems use DMA (if the capture card is a PCIe device) to transfer data and this should be controllable in some places in the capture card drivers. But such a hack would not be straightforward. Probably another solution will require less time and might be sufficient too. Maybe you can interface the capture card with USB or a card reader (micro SD or something?), but this is speculation since I do not know what a capture card exactly is in your case.

Dave says

Hi Tim,

Thanks very much for your very detailed posts. I came here after reading your (usefully super-detailed) post about which GPUs to use for deep learning. Based on that, I’ve decided to get a 1080Ti. I have a very naive question, as I look around on Amazon (for example), it seems that various vendors sell these, including EVGA, MSI, etc. sell a “1080Ti”. Is one of those optimized for deep learning more than others? Sorry for such a naive question, and thanks again!

Tim Dettmers says

The brands often add special features, but essentially they all work with the same microchip and all have the same performance. Do not be confused with “high clock” versions, these version improve performance for gaming but not really for deep learning. So you can buy any GPU from any of the brands, and practically, I would just go with the cheapest one.

foojpg says

Hi Tim,

Does GPU memory (VRAM) stack when running machine learning algorithms? By this what I mean is, if I have eight GTX 1080 TIs (with 11GBs of VRAM each), will I have a total of 88 GBs of VRAM in my system? Or does it work like with gaming and SLI – the VRAM doesn’t stack up and the total VRAM in the system is only 11GBs?

Thank you and I love your blog 🙂

Tim Dettmers says

You can achieve such behavior by using model parallelism, that is splitting your model among many GPUs, but this is usually not supported by software. Usually you have similar behavior as with gaming and SLI where the same model is run on all GPUs and thus it is limited to the amount of RAM on a single GPU.

Guenter Huber says

Hey Tim,

in the light (hopefully 😉 of your nice article I wrote a short note on

https://medium.com/@gue22/supercarrier-motherboard-mothership-for-deep-learning-c88c51c44100#.briv8ku3a

about the upcoming ASRock Z270 SuperCarrier motherboard and what shiny machine would be possible.

Tim Dettmers says

Thanks for your comment and blog post. The new motherboard looks nice and shiny, but I am not really convinced. There is a lot of fancy stuff on the ASRock Z270 SuperCarrier that you do not really need. I am not a big fan of DDR4 boards. It adds almost no improvement in deep learning performance and you have an expensive motherboards, expensive RAM, expensive CPUs which often lack full lane support. I rather buy a cheap DDR3 board, preferably from eBay, which will lend maybe 95% performance but will also save you $300-$500. For such boards it is also easier to find a 40 lane CPU that is needed for 4 GPUs.

Guenter Huber says

Thanks for your input!

Isn’t the 4-way-SLI supplanting the slower PCIe? Do you know to what extent?

Phil G says

SLI does’t apply to deep learning. NVlink may make a difference in the future, but that’s probably 3 to 5 years away for consumer boards.

angy says

hi Tim,

I read this blog.I want to make sure about my conclusion from the blog about building a multi-node multi gpu system for deep learning on windows platform:

basic requirements for this: 2/more gpus on 2/more computers/systems/nodes, cuda toolkit, caffe/theano/tensorflow…. backends, inifinibands.

I want to make sure about the mandatory requirement of infiniband.. Is it mandatory or just to provide higher data transfer rates? Is it not possible to build multi node multi gpu system just by using ethernet/wireless connection without any infiniband; no matter what the transfer rate will be?

Tim Dettmers says

Yes, bandwidth is the main issue. If you use Microsoft CNTK with its efficient 1-bit algorithms then Ethernet might work okay (which means 4 GPUs may give anything between 0.4x-2x speedup), but generally the bandwidth is just too low. Especially for wifi the performance for multiple GPUs will be lower than for one GPU. Another thing might be latency issues; these might arise for Ethernet and destroy performance. In short: I would not rely on Ethernet if I want to do parallelization for deep learning.

In general I would recommend to go for a 4 GPU pc for parallelization, rather than multiple PCs. It is just a big, big hassle, is expensive, you need special software, and the speedup is not that great in the end. Not worth it. If you still want to go for it, definitely get Infiniband cards.

Kewen says

Hi Tim,

Your blog is awesome for me and I learned quite a lot. Here are 2 options for system choices: 1 node with 8 GPU (Enabled with PCIe switch chipset), or 2 nodes with 4 GPU each.

Which solution you will prefer?

Thanks,

KW

Tim Dettmers says

The 8 GPU system will be faster, but much harder to use. To parallelize efficiently on 8 GPUs you would need to bring the memory back to the CPU and aggregate it there. This can be done without much loss of performance with certain parallelization algorithms, but most frameworks do not offer this solution (CNTK being the exception). I personally would got for the 2 node 4 GPU option, simply because existing software will be easier to run. Although only CNTK and Tensorflow officially supports across node computation, so the goal of parallelizing across 8 GPUs should only be a goal if you really need that speed. For most application 4 GPUs will be rather okay.

Tlund says

Tim this blog is amazing. Thanks for the amazing info. You may have answered this but I don’t think I quite grasped your answer s in the comments above so I want to make my questions more explicit:

1\. If I am training a SINGLE large conv net, will a dual Pascal titan x setup in “sli” mode be faster to train the model or will training the net on a single titanx pascal be faster?

1a. Does sli mode trick software into thinking there is only one GPU? If so will that cause huge speed up?

2\. Is a multi GPU setup ONLY good for training different models in the deep learning context?

Tim Dettmers says

1\. For convolutional nets, especially ones without fully connected layers, 2 GPUs will be nearly twice as fast as 1 GPU

1a. SLI is a concept that is only relevant for visual display but not for compute. With CUDA you can use multiple GPUs any time — no SLI bridge required

2\. See (1.); generally modern models benefit well from multiple GPUs, so if you want faster training and you have the money, you should go for 2 GPUs over a single one (or even more than two if the money permits, of course)

Lomov says

Hi Tim,

At the moment, I’m planning to build new workstation to start deep learning, possibly go into research path. I have major in machine learning but not much experience with deep learning so it is unclear to me

– whether it is possible to run one deep learning algorithm with a multiples GPUs attached to single CPU and benefits the speed up. For example, will a machine with 2 titan X be 2x faster than the one with only 1 titan X, is any bottleneck ?

– I’m still in the state of planning all the components (mobo, ram,cpu,gpu…) so I want to make sure that I’ll spend money efficiently according to my need. Will you recommend buying 4 gtx 1080 over 2 titan X pascal (more memory,nearly same price) ? Or even 3 gtx 1080 over 2 titan X (same amount of memory, cheaper).

– Since there’s possibility that I will go into research path, and if it is so, I will probably run multiple algorithms on different GPU to test the efficiency of the model parameter. Is it possible with single CPU? If it’s possible, will different GPUs work? let’s say now I purchase titan X pascal and in January, I will purchase 1080ti with same amount of memory but cheaper. Will two different cards be able to run two different algorithms on a single machine?

Really look forward to your reply!

Tim Dettmers says

One CPU will be sufficient for 4 GPUs – so there will be no problem. The 2x Titan vs 4x GTX 1080 issue is not straightforward; some algorithms will only run on the Titans not on 1080s. This depends highly on the application. I recommend to start out with a single GPU and upgrade later. You could get a GTX 1060 to get started and figure out if you need more memory or not for your research applications. After you know what you need sell the GTX 1060 and go for Titans for GTX 1080 (or wait for Volta).

mesin hitung uang says

Aku ingin mengucapkan terima kasih untuk ini baik baca !!

Saya benar-benar menikmati setiap sedikit itu. Saya memiliki Anda buku ditandai untuk

memeriksa baru hal yang Anda posting …

zhaoyj says

HI,I’m installing cuda on ubuntu 14.04 ,and my machine is equipped with 4 GTX 1080 gpu.But there is a problem that I still can not tackle,that is,when I have installed cuda and NVIDIA driver(367.35),and my machine can detect them,however,I can no longer login in my desktop,always a login loop problem.After searching the internet ,I think there may be something wrong about my xorg.config file, neither auto-generating xorg.config file nor just removing it can make effect,so,my question is,is it necessary for me to manually configure the xorg.config file,if it is,then how?It would be of much help if anybody could share with me your solutions,thx!

Tim Dettmers says

I had some problems like that before, installing those drivers can be messy. However, there should be a new ppa which is designed for nvidia driver install and which should work flawlessly. I do not have the exact commands, but you might find them quickly using a google search. One thing that comes to my head, is that you should disable the X-server when you install your driver, if you did not take this step you might want to try that.

Fakenamesorry says

Understood, thanks for responding so quickly!

Fakenamesorry says

Since the GTX 1080 has slightly less bandwith then a 980 TI, is the 980 TI the superior card for deep learning?

Tim Dettmers says

No, the GTX 1080 is better. You cannot compare the bandwidth between GTX 1080 and GTX 980Ti directly, since they are based on different chipsets.

Jay says

Hi, we’re you able to get Gpu Direct working using the GTX Titan 6GB. Between two computers .Thanks a bunch.

Tim Dettmers says

Yes I did get it working with a Mellanox Infiniband card, but it took quite a bit of work. You will need the Mellanox GPUDirect driver and the Mellanox suite. Then it is a lot of configuration and stuff. Took me a couple of days, but I guess with the newer cards it will be straightforward to get everything working.

Jianri Li says

Hi, Thanks for nice postings.

I have several questions about 4 -way Titan X system.

We are planning to build a custom system with 4 Titan X GPUs and two Xeon CPUs.

And I have 3 questions.

1\) In previous replies, you said one CPU is enough for 4 Titan X, but one CPU will only provide 28 lanes (Core i7) or 40 lanes(Xeon) for max, while 4 Titan X requires 64 lanes (at PCI-E x16 mode ) or at least 32 lanes (PCI-E x8 mode). Will not 4 Titan X system at PCI-E x8 become a bottle neck for deep learning ?

2\) How could you handle with cooling problem in a 4 Titan X system ? Is is related to system stability?

3\) If I use Ubuntu 14.04, will the NVIDIA driver normally recognize 4 GPUs ?

Thanks a lot.

Tim Dettmers says

1\) If you use 2 CPUs you can use 16x lanes per GPU but you will need to pipe the GPU memory through CPU memory to access the GPUs that are attached to one CPU from the GPUs from another CPU. Overall, you will lose performance when you use 2 CPUs for 4 GPUs.

2\) If put the fan speed to max it will be quite okay, for that you will probably need to make some hacky changes to the NVIDIA xorg config

3\) Yes, that should fine without any problem

Jianri Li says

Thanks for your reply !

There are a few things changed in spec. We will replace Titan X with GTX 1080, which means there would be four GTX 1080 gpus.

Now I think the only problem is cooling. I have read all your posts in your blog, but still few questions remain.

1\) We won’t connect any monitor to GPUs, and we will install Ubuntu Server version which does not contain any x11 programs, all access will be through LAN cable. Is it OK to use? (actually there will be no xorg file … now I am working with ubuntu server + K40, and there is no xorg file, fortunately K40 is passive cooling)

2\) In your first post, you said “to change fan speed in multi-gpu system, one had to update gpu bios …” is this still needed to update bios in recent gpus ?

3\) Is there any risk to re-flush gpu bios? like losing warranty or permanently destroy gpu ?

4\) If constructing a 4-way system is too hacky , I will choose a 2-way gtx 1080 system (which is still even much faster than 4-way titan if FP16 is enabled). In this case, is the setting for fixing fan speed to maximum still needed? (Assume distance between two PCI-e slots are quite OK, for example, two pci-e slots placed at 1st and 4th bay)

5\) Do you have any plan to upgrade your system to gtx 1080?

Thanks again!!!

Jianri Li says

Another Question 🙂

How can I monitor GPU temp in ubuntu ?

(K40 info could be found in nvidia-smi, but for desktop gpus, nvidia-smi may not work? does it?)

Roberto Paredes says

Hi Tim, congrats for this very interesting blog. I am developing my own deep learning toolkit for CPU’s trying to optimize it at maximum and obtaining competitive results on small convolutional nets. Why? Because my students have to work on cpu machines and i would like to provide them a reasonable speed but with a very fast learning curve of the basic deep learning tools. Caffe, Torch and others provide IMHO a slower learning curve.

My question is, under you expert point of view, do you see any future on CPU computing for DeepLearning? What about the Xeon Phi cluster you mentioned?

Thanks a lot!

Marc-Philippe Huget says

Hello Roberto,

Personal view on your question: since companies invest a lot on clusters and servers, they have plenty of CPUs to use even if it is slower than GPU (NVidia co-founder mentioned a NVidia Drive PX-2 worth 150 MacBook Pro…), so I guess CPU computing for Deep Learning is possible, but now is it affordable?

Regarding framework, Keras and Lasagne are easier to use and understand for students, maybe you should check them

Cheers,

mph

Roberto Paredes says

Hi Marc, thanks for your comments. I know the frameworks you mentioned, But now i have my own very finished and ready to put on github. It is quite easy to define a net, something like:

network N1 {

data tr D1

data va D2

// Covolutional imput

CI in \[nz=3, nr=32, nc=32\]

// conv

C c0 \[nk=64, kr=3, kc=3\]

//pool

MP p0\[sizer=2,sizec=2\]

C c1 \[nk=128, kr=3, kc=3\]

MP p1 \[sizer=2,sizec=2\]

C c2 \[nk=256, kr=3, kc=3\]

MP p2 \[sizer=2,sizec=2\]

// FC reshape

F f0 \[\]

// FC hidden

F f1 \[numnodes=128\]

// FC output

FO f2 \[classification\]

// Links

in->c0

c0->p0

p0->c1

c1->p1

p1->c2

c2->p2

p2->f0

f0->f1

f1->f2

}

Regards!

Marc-Philippe Huget says

Dear Tim,

Have you made any progress on your multi-GPU system? Any news to share with us about that?

Thanks in advance,

mph

Tim Dettmers says

I disassembled and sold my multi-GPU system when I moved to Switerland. However, currently I am working on a cluster of Xeon Phis and probably soon also a cluster of GPUs for which I am currently developing software (Tensorflow benchmarks are rather poor, I think I will be able to improve upon that, but it will take some months to get the library into a state which is useful to others).

Dave says

I’m using 4 Titans on an Asus X99-E WS . Is there any way to get more than 4GPUs on a single machine (a PCI expansion box comes to mind, but would Caffe recognize 7 GPUs)?

Tim Dettmers says

The problem here is the PCIe limit on your CPU. You will need two CPUs for 8 GPUs, or alternatively, you could buy “dual-GPU” cards like the GTX x90 cards. Using dual-GPU cards is relatively straightforward and most software will support, however not so if you two CPUs. I would recommend to stick to 4 GPUs, the trouble of more GPUs is only worth it if you scale out even more (say 12-24 GPUs or so in multiple computers).

vinjohn says

Hi Tim,

Learned a lot from you blog..

I am a student and new to deep learning, planning to get a laptop with 980m sli or 980(notebook version, it’s the same with desktop version).

I know that sli has no improvement for deep learning, but what if I disable the sli and use 2 980m instead?

So my question is will two 980m better than a single 980? 980m and 980 are both 8G.

980m(1536 cuda cores) is just a little less powerful than 970(1664 cuda cores).

Looking forward to your reply!! much thanks!

Tim Dettmers says

You do not need to de activate SLI, it just works independently from normal CUDA operations.

Regarding 2x 980m vs a 980: If you have good software for parallel training the two GTX 980m should be slightly faster than a single GTX 980. However, for many architectures there is no such software and in that case a 980 would be about 30% faster. The two 980m are more useful if you want to train different architectures at the same time. So these have both advantages and disadvantages, no choice is really better than the other.

Seyed says

Hello Tim,

We want to build a 25+ cluster with GTX980Ti’s, Could I connect them with ConnectX2 cards?

And is it possible to use the the dual port QDR ConnectX2 card for TCP and IB at the same time for GPU to GPU connection, we want to use one dual port card for 20Gb/s IB and 5Gb/s TCP/IP for the data transfers. Of course we want to use two infiniband switches for it.

One for the IB and for the TCP/IP.

I am kind of new to the ConnectX so I would appreciate any help you can give me.

Tim Dettmers says

I got RDMA GPUDirect working on my ConnectX2 cards, but it is not support by Mellanox so you have to hack yourself through that, so I recommend that you first get a small system and test all the technicalities before you expand your system.

Using two ports at the same time should work, but you should be aware of possible performance bottlenecks. With two ports you will have four messages per GPU pair that will compete for a lane to the network card. If there are some latency issue this might be a considerable bottleneck due to waiting time on consecutive messages, but I have never tested myself nor seen data on this kind of setup. So again, getting a small system (2 computers with 3 GPUs each) and testing if everything works might be best before you make the step to buy the whole system. If you need to push ahead and order the full system at one time it might be best to just get some good FDR cards with ConnectX3 or better which have active support for RDMA GPUDirect. However, if you do this then the bandwidth on the PCIe will be the bottleneck (8GB/s vs 14GB/s for 2 FDR ports), so in that case two ports make no sense.

Hope this helps.

Ross says

I’m building a workstation with 4 Titan Xs. Am I better off with 1 processor, or, is it going to be OK to have 2 processors with the GPUs split between them?

Tim Dettmers says

One processor will be better. Two processors can complicated the PCIe layout which might make your deep learning software that feature parallelism slower. One CPU should be sufficient for 4 GPUs.

Poornachandra Sandur says

what is the minimum required gpu for a beginner to build Deep Learning algorithms in Medical Image Processing area ???

Tim Dettmers says

This depends mainly on the size of the images and the size of the data set. When I look at Kaggle competitions I see that medical images usually have very high resolution, which means that you need a GPU with 6GB or more. However, you could always shrink down those images and use a 4GB GPU, but your results will be worse. Also see my GPU advice post for more information.

Tao says

Hi Tim,

I’m also working on medical images. I got a Titan X with 12GB memory. And I’m working on CR images with resolution of more than 3000×3000.

At the begining, I resized all the images to 256×256 (so that I can easily do transfer learning using the pre-trained imagenet model).

And then I realized 256×256 is not enough for my classification task. So I tried a 512×512 model. But there seems no improvement.

Can you suggest how to do image classification for high-resolution images?

Thanks

Tao

Haider says

I had the same question of Greg’s to use VirtualBox to install Torch in Ubuntu inside Windows 8.1 . And I liked his previous post about the divide and conqur way to scale up in a stepwise fashion to build a high end system eventually but slowly, and learn about deep NN in the meantime. My plan is almost the same.

I think his query and mine is because currently, we have only one powerful Pc and Windows is very essential to us to run several other software, and it is not easy to make it as a dual boot with Ubuntu, since Deep NN experiments will take days and we cannot afford a dedicated Windows Pc.

Do you know whether there is a way to run Torch7 in Windows? How about Caffe ?

You was saying that “The virtualization only allows on some hardware combinations to do GPU computing on a virtual machine”.

What are those hardware combinations? I have core i7 3770K, 32GB RAM, Z77X-D3H mainboard. Does this hardware combination allow me to use Torch with GPU computing?

I am thinking to use just the CPU currently for getting to be used and learn Torch, but later on maybe I will buy a Titan X and use GPU computing.

Thanks for the thoughtful blog posts Tim!

Tim Dettmers says

There are ways to run Caffe under windows (I never tested them, but it seems very possible); running Torch on windows is rather problematic and I would not recommend trying that.

The hardware you need is a CPU with virtualization support — and very important — the GPU must also support virtualization. I think currently only the NVIDIA GRID series GPUs do have such a support.

I think overall your best bet would be to run a deep learning framework on windows (besides Caffee, Theano should work too).

Greg says

I have a super fast desktop…what are your thoughts on running a VirtualBox and installing ubuntu and Torch on that? Slow as ice melting and no good for machine learning?

Tim Dettmers says

The virtualization only allows on some hardware combinations to do GPU computing on a virtual machine; also the performance is often poor for PCIe connections (just like on AWS), so I do not recommend using a virtual machine for deep learning.

Greg says

I was thinking to tackle this in a stepwise fashion.

I have a core I7 Win 7 laptop I could perhaps install and learn to use the software; yet, I am not sure on the software packages as there are many.

I think you mentioned Red Hat and the Nvidia devbox software list mentions Ubuntau plus other apps like Theano, Torch, etc. So I’m pretty lost. I want to make the best choice but the details are fuzzy.

During my learning of the software and algorithms on the laptop I would begin building the new machine.

I saw the NVIDIA® DIGITS™ DevBox demo and I am hoping that whatever software I begin to learn will scale to that demo and beyond. The demo however concerns me as it and all demos I have seen only deal with photo or speech rec and neither seem close to what I’m interested in crunching.

What do you suggest? Do you think this idea of divide and concur a sound idea?

Thanks in advance for your time and feedback…

Tim Dettmers says

I would use Torch7 and ubuntu 14.04. It is not only the most productive setup that there is at the moment, but probably also the easiest to use and the one with the most features. So with that combination you will have a versatile, productive system with an okay learning curve.

Greg says

What do you think of the NVIDIA® DIGITS™ DevBox?

Specifically the list of both hardware and software? (I’ve attached for your review)

DIGITS DevBox includes:

• Four TITAN X GPUs with 12GB of memory per GPU

• 64GB DDR4

• Asus X99-E WS workstation class motherboard with 4-way PCI-E Gen3 x16 support

• Core i7-5930K 6 Core 3.5GHz desktop processor

• Three 3TB SATA 6Gb 3.5” Enterprise Hard Drive in RAID5

•512GB PCI-E M.2 SSD cache for RAID

•250GB SATA 6Gb Internal SSD

• 1600W Power Supply Unit

• Ubuntu 14.04

• NVIDIA-qualified driver

• NVIDIA® CUDA® Toolkit 7.0

•NVIDIA® DIGITS™ SW

• Caffe, Theano, Torch, BIDMach

https://developer.nvidia.com/devbox

Tim Dettmers says

This is the best 4 GPU system, but by far also the most expensive one. I do not think the price/performance ratio is good, but for people that have the money and are too lazy to figure out what they really need it is a good option.

Greg says

HI…I’m pretty lost reading your posts…sorry…in that I can’t make out what you recommend. You point out too much and loosely discuss what you think is good vs $$$. It sure would be a lot easier to follow your recommendations if they were laid out in some sort of table maybe cost versus performance …or something like that.

Overall great posts….thanks!

Tim Dettmers says

Thanks for the feedback! I will try to make things clearer with an update. Here a simple algorithm how to find the best GPU.

Generally, there are two questions you need to answer yourself: (1) How much money can I spend? (2) Am I going to work with data sets > 200GB?

If (2) == Yes then your only options are 6GB or 12GB GPUs.

For (1) go to here and look one by one, from highest bandwidth in GB/s to lowest bandwidth in GB/s; Choose the GPU with the highest bandwidth that you can afford (1) while taking (2) into account. If you cannot afford any GPU there, go to the GTX 700 and repeat.

Then there is also eBay which makes things cheaper, but for newer GPUs the price difference is negligible, and so the algorithm above should most often yield the GPU that is best for you.

Does this make things clearer, or is such a rule-based formulation confusing as well?

Greg says

Yes, clearer thank you.

I cringed when I saw the price of the TITAN X GPUs with 12GB of memory but I think it’s best to get something that is cutting edge now as it will become outdone by something new in a few months.

Thanh Tung says

Hi Tim,

I am a beginner in the field of deep learning and I want to buy a laptop to try out some deep learning algorithms such as Convolution Nets, Neural Turing Machine and do some Kaggle projects. For now, I have some options:

Alienware with GTX 970M or

Thinkpad W540/Dell Precision with K1100M

Which laptop do you think is better?

Thank you

Tim Dettmers says

I do not know about the laptops per se, but a GTX 970M will be much better than a K1100M for deep learning.

Thanh Tung says

Thank you. i will get a GTX 970m :). My room is too small for a desktop so a poweful laptop is my only option.

lU says

Hello mr. Tim,

I’m trying to assemble a cheap system with which i would try out some of that deep learning wizardry.

I’m trying to build something cheap around a gtx 780. Do you think the choice of a CPU matters that much? appart from when you compile your code to run on the GPUs, is the CPU under any load when the neural network trains? how much time does it typically takes to compile the code for a neural network that would take several hours to train?

Tim Dettmers says

The CPU choice can be complex, but I will post a new blog entry in the next days which will deal exactly with this topic — so stay tuned!

Cherry says

My bad. I think the right one would be FDR ConnectX-3 cards and QDR ConnectX-2 cards…

Cherry says

Once again, thank you so much for all the help, Tim! I will be watching out for your new updates for sure! :)) And it won’t be long before I will be stealing your bit of MPI code there. 😉

Cherry says

Hi Tim,

I’m a little bit confused. If you say we can only connect two Quadros directly, then if we buy, for example, GTX Titan Blacks, won’t we have to route the data through the CPU which will be slower? To my understanding, Infiniband GPU-direct enables CPU bypass. So if we are to use that, we can only buy Quadros now, right?

It would be great if buying Titan Blacks can still be an option though…

We won’t be sharing this hardware with other departments, but it would be great to be able to create large convolutional nets.

timdettmers says

Yes, I have been a bit unclear on that. I think it might be cheaper to “waste” the two Quadros you already have, i.e. sell them or “put them on the pile of outdated hardware”. That hurts a bit, because Quadros are not cheap, but on the bottom line you will have a cheaper and more powerful system this way (which has less memory of course than 6 Quadros would have; but again 4 additional Quadros are more expensive than 6 Titan Blacks).

Cherry says

Thank you so much for all the recommendations! It’s really a lot of help!

I just found out from my colleague that Titan Blacks have been discontinued already? (I looked for it on amazon, and there are only 1 or 2 new pieces available. On top of that, we’re in Korea right now; if we want to assemble 6 Titan Blacks, we would have to get them from different sellers, and ship them here.)

Due to time and budget constraints, our choice now is either to find out whether we can actually get assembled GTX980s (to be able to get more GPUs) together with FDR ConnectX-3, or stay with Quadro, downgrade some other specs, and get FDR ConnectX-2…

timdettmers says

You are welcome! I did not know that it was so difficult to get a handle on Titan Blacks. That is a tough decision you have to make there, but I would probably would go for the GTX980s if available. Such a system would also be easier to upgrade than a system of Quadros. However, if you aim to train really, really large convolutional nets the Quadros might indeed be the better choice. But I bet that will be an impressive system either way!

Cherry says

We are trying to build a GPU cluster to do deep learning with and currently, we have two NVIDIA Quadro K5200 GPU’s, two CPUs (16 cores). We are thinking of expanding the system by buying another CPU+GPU set, and of course, the Infini-band cards (GPUDirect RDMA). However, since we’re new to deep learning and don’t have much idea on how to set it up, it would be great if we can get suggestions on which hardware to buy. I read somewhere that Tesla is the best right now (particularly K40 –Ian Goodfellow), but I’m hesitating because there may be incompatibilities if I try to connect Quadros on one station and Tesla on another station.. Also, Tesla is a bit expensive. Will it be a better decision to get Quadros again this time? Will it be better to just get one GPU to add on the existing machine, instead of getting two GPUs on a separate machine? And if the latter is better, is Mellanox ConnectX-3 the fastest one (or the most recommended) and how many cards do we need to connect two stations? I read on your post too that we need fiber cables…

timdettmers says

You need the same kind of GPU chipset in order to communicate with both Infiniband RDMA and NVIDIA peer-to-peer GPU-Direct – in other words it is essential that you have the same graphic cards (but you can choose different brands like ASUS + EVGA etc.). Of course the K40 is the best GPU, but it is not very cost efficient. It has high double precision FLOPS and memory correction – both expensive features which are not needed for deep learning. If you can wait until March and can buy the very cost efficient new 12GB GTX Titan X (or whatever it will be called). That GPU should be much faster than the K40 and much cheaper. Another Quadro will be a good choice to prototype the system (one GPU for each computer until you figured everything out, then buy new Titan Xs).

In terms of Infiniband cards you should buy the best cards you can afford; FDR cards are preferred over QDR. Mellanox has new EDR cards which have twice the performance of FDR – but nobody knows how reliable they are. If the new EDR cards work it will be a huge step for deep learning, but I guess those cards will be expensive (and the switch even more so). I never worked with double port cards; if one can get them working this would also be a huge improvement – so maybe you should look into that.

As long as the card is ConnectX-3 or better you will be fine. You can use copper cable, if your computers are not too far apart (less than a few meters); if they are further apart you will need fiber optic cables. The cables should have the same grade as your card (QDR,FDR,EDR (it might be hard to get EDR cables; EDR is very new).

GPUs per computer is a difficult question. It all depends if you can keep them cool and what your mainboard can hold. For large scale deep learning, you want to build a system with as many GPUs as possible for each computer (on standard hardware this will be 3 GPUs + 1 Infiniband card).

Cherry says

Hi Tim,

Thanks for the fast reply! Really grateful for all the help.

I have a few follow-up questions and clarifications, though. When you said, “it is essential that you have the same graphic cards (but you can choose different brands like ASUS + EVGA etc.)…,” did you mean we should get NVIDIA GPUs only since we already have Quadros now? And you mentioned that, “…then buy new Titan Xs.” So we can get different GPUs to connect as long as it’s NVIDIA?

We currently have 2 CPUs (Intel Xeon E5-2630V2). Will this be able to hold 3 GPUs in one computer? Or will we have to see for ourselves if the 3-GPU set-up can stay cool enough?

Sadly, it’ll be a bit hard to get a hold of Titan X’s. Our budget is only until this month, and we also have to order them as soon as possible…

So as I understand it, for a two computer set-up, it will be:

heavy-duty CPUs

3 GPUs for each computer (max)

1 Infiniband card for each computer (FDR)

Copper or fiber cables (FDR) (how many should we get to connect two computers?)

We will be getting Mellanox FDR ConnectX-3 (GPU-Direct RDMA) cards as you suggested. Thank you so much for that!

timdettmers says

Hi Cherry,

what I meant was that you need the same GPU chip to communicate between GPUs, this means NVIDIA Quadro K5200 can only communicate with other NVIDIA Quadro K5200 directly, otherwise you will need to route the data through the CPU which is slower.

Dual CPU mainboards can be complicated. Theoretically, it could be possible to run 8 GPUs with 2 CPUs on one board if each CPU runs different PCIe lanes. However, I think you will be limited in PCIe x16 slots. Modern GPUs have a width of 2 PCIe slots which means that you will need a mainboard with 7 PCIe slots to run 3 GPUs and an Infiniband card. One way to utilize all PCIe slots is to use PCIe extenders (which would also help to keep the GPUs cooler) but then you will probably need to build a custom solution where you can mount the GPUs outside the mainboard.

To be clear, one CPU can only manage 40 PCIe lanes divided among all PCIe slots (8x8x8x16 is common for a 3GPU+Infiniband setup); 40 PCIe lanes often equals to active 4 PCIe slots. So if only one CPU is connected to your PCIe slots, then you will have a maximum of 4 devices instead of 8.

If you have to order quickly the best choices are:

– for speed: 6 GTX980s (fastest cards; cheap; 24GB memory)

– for double precision (if you share your hardware with engineering departments for example) and large memory (for very large convolutional nets): 6 GTX Titan Black (fast; price okay; 36GB memory)

– you should buy Tesla only if you share the hardware with departments that need very high precision (engineering, differential equation modelling)

– you could buy more Quadros, but those cards are expensive and slower than Titan Black (they have more memory though)

Ali Razavi says

Hi Tim,

Thanks for the informative post. I am wondering what mother-board you used? I also read somehwere that only the Tesla line supports RDMA GpuDirect, has that changed?

timdettmers says

Most motherboards will do. If you use only one GPU a PCIe 2.0 motherboard is okay although a PCIe 3.0 board will be better (a slow down will occur when you push data from your CPU to our GPU – this slow down is often insignificant when compares to the performance of the GPU). When one uses multiple GPUs you should make sure that your motherboard supports PCIe 3.0.

I myself used a ASUS Rampage IV extreme – with which I made poor experiences (could not get a 4 GPU setup working; the customer support was not helpful); however, other people could get 4 GPU setups working on this board without any problems. My other computer uses a Gigabyte Ultra Durable 5 which is okay and works just fine.

Edit: Yes indeed, RDMA is only supported for Tesla products and Mellanox ConnectX-3 cards; however, there are many instances where people could get it working with non-Tesla, Kepler cards and Mellanox ConnectX-2 cards. This motivated me to build my system, I also used normal Kepler and Mellanox ConnectX-2. I saw hacks where people could get it working on even older hardware, but there will be more difficulties I presume. Any combination of Kepler card and ConnectX-2 card should work with some tinkering.

John says

Thanks a lot for the information. I have a few computers with GTX 780 Titans and I want to try this. Could you please let us know more details about which NVIDIA and Mellanox drivers that you installed and where you downloaded them? Which OS are you using?

timdettmers says

You should definitely use a Linux based operating system like red hat server(I think this is officially supported) or ubuntu (I used ubuntu). Installation can be difficult and there is no easy recipe. I could not get RDMA for MPICH working, only OpenMPI – but this might be different for you. I installed the Mellanox NVIDIA peer driver and the OFED framework. I needed many days to get everything running. You might find parts of the solutions on other blogs and forum posts; Google is your friend here. The biggest hurdle for me was to get the Infiniband cards correctly identified by the software; after that I changed the system step by step with the benchmarks and stopped when it was working.

Richard says

I don’t know if anyone else here has experience working with GPUDirect RDMA, but I’ve been tinkering with it a bit for the last few days, and it seems to be disabled on GeForce boards. And officially it is only availble for Quadro and Tesla hardware. I guess it might be a driver limitation, and eventually it could work when modding the GPU to advertise itself as a Quadro device, ….

Anyways, if anyone had success with getting GPUDirect RDMA working on a GeForce card, I’d love to hear about that. 😉

timdettmers says

It can be difficult to get RDMA working on Kepler cards, but it is not impossible (you must have at least ConnectX-2 cards). I think for me was the trick to install nvidia peer driver, a beta Mellanox driver for Kepler cards.

Grant says

Yeah, I was a bit shocked when I saw the FDR switch costs…but I guess like all good computing tools…over time their prices will plummet like a rock:) Not comforting in the immediate term though. I really wanted to try and build something scalable….and it has turned into a real challenge…both price wise and system wise. Power and electricity becomes a problem relatively quickly for something like this.

In the last couple days I decided to experiment with some Xeon Phi cards, and trying to build a system for those, and this is an additional nightmare as the motherboard has to support large BAR encoding, which means $$$:( But I’m interested to write code for these, even though right now the best Nvidia cards will destroy these. So I’ll persist. If I get it all to work I’ll post a writeup somewhere. Thanks for all your help!

Grant says

So for the infiniband card…which 40gig card supports GPUdirect RDMA? Is this strictly the FDR Infiniband? Any help/advice would be greatly appreciated, I’m working on building a small research cluster right now.

timdettmers says

RDMA is independent from the bandwidth of the card, there are some QDR cards (like I have right now) that support RDMA. RDMA for GPUs is a joint development between NVIDIA and Mellanox and Mellanox ConnectX-3 generally support RDMA. However, the card that I have is a ConnectX-2 card and RDMA works for me just as well. I have seen people get to work RDMA under different cards, but there are no guarantees and it can be very difficult to get it to run properly.

In short:

– Any Mellanox ConnectX-3 cards will do

– You can try ConnectX-2 cards if you do not have the budget for ConnectX-3

– Stay away from other cards if possible

Grant says

Tim, thanks so much! I have been scouring ebay and reading as much as I can. I’ll definitely look to find some of the connectX-3 or x-2 cards. I am trying to avoid as many of the software complexities as I can, so just trying to find the most compatible hardware to hopefully alleviate as many headaches as possible. In terms of a switch…do you think any QDR switch will do? I’m looking to hook up a few servers so I’ll need to grab one of these as well…which is another big expense:(

timdettmers says

A switch is another big investment, indeed! I thought about creating a cluster with more nodes, a switch and smaller GPUs, but the switch was so expensive that a two node cluster with fast GPUs was the better option for me. So I do not have experience with Infiniband switches, but I believe there should only be a minor difference between one switch and another, say 5-10%. Also I say them sometimes quite cheap on eBay, so it is worth to check frequenctly for that. You might want to start with two nodes, and extend your system once you snatched a cheap switch off of eBay.

Besides that, when you build a bigger system, keep in mind that networks get more and more expensive (because information needs to be synchronized among all machines), so FDR cards + switch is a good investment for larger systems (if you can afford that).

Another thing I did not think before building my system is using cards with two Infiniband slots. I am not sure how it works on a software level, but two ports means two times the bandwidth on a physical level, and I am sure that will translate in similar bandwidth increases on the software level. Maybe you can look into that also.

dan says

hi tim.. thanks for the great guide. i’m building a single computer with four titan x gpu (single computer, no cluster).

1\. do you recommend adding an infiniband? from your photo, it looks like you have 3 titan and an infiniband. do gpus within a computer communicate just through pci-e 3? or do they also communicate via infiniband as well (within a computer)? if so, what would be the speedups?

2\. would you recommend to build a single computer with a lot of GPUs (say 4 or 8 titan x) or building a small cluster of 2 computers (with either 2 or 4 titan x) each? it looks like you ran an experiment on a 2-node cluster. i’m curious to learn what’s your thought after the experiment. for deep learning, it seems to me like a single computer with 4 or 8 titan x would be more than enough, unless there is a good reason to setup a cluster?

thanks.

Tim Dettmers says

1\. Infiniband is only useful if you use more than one computer; it is basically the same as a ethernet connection between computers, only quite a bit faster

2\. Get 4 GPUs in a single computer: Most motherboards are limited to 4 GPUs and very expensive, special motherboards are needed for 8 GPUs in one system. A 8 GPU cluster is a lot of more work to get and keep it running; you will need special software (you cannot use theano or torch for that) and the system needs to be tweaked in detail. Thus 4 GPUs is the cheapest, most easiest to use and most practical solution. So get a 4 GPU system.

However, you might want to build a smaller system instead and save up your money for the Pascal GPUs which will come in late 2016. These GPUs will make all those that did come before them look silly.

Farahana says

I’m sorry if this was answered or posted already, is the PC and theano directly recognized 2 or 3 GPUs in our system (1 PC only), or we need to make it work? Thank you.

Tim Dettmers says

If your OS recognizes the GPUs so should theano. Make sure that you have selected all the GPUs you want in your .theanorc config file.

dan says

thanks tim for the quick reply. why are both torch and caffe only running with 4 gpus? i’m writing deep learning from scratch, so it doesn’t matter much. but i’m just curious to understand why both of them are only limited to 4 gpus. any specific reasons?

btw, late 2016 is really far away. that’s 1 year and a half 🙂

Dr. Aparupa Dasgupta says

Interested to know about annotator

timdettmers says

Sorry, but I do not get what you mean with annotator. Can you please elaborate?

Aparupa Dasgupta says

The Institute’s group, I am associated, are into R&D in NLP (specifically on Machine Translation). We are finding a way to build POS tagger (specifically on Indian Language) for annotating any unclassified or unlabeled text/data. I am interested to know about Deep Learning / Neural networks to build annotator / POS tagger.

timdettmers says

Developing a POS tagger for Indian language is a very interesting problem. I aim to work on similar problems myself in the near future. If I have any results I will post them here on my blog.

Atcold says

I am not sure I understood which software you did use. Torch, Caffè, others? Or you coded stuff yourself?

timdettmers says

Thanks for your comment Atcold. I coded the stuff myself to get a better understanding of the bottlenecks for computing with multiple GPUs and a GPU cluster. It is rather difficult to understand the low level details when one starts with a larger frameworks as Torch7 or Caffè.

Variasi Motor says

This was answered elsewhere but why did you opt for multiple systems

timdettmers says

My main interest was to identify the bottlenecks in hardware and software in a multi-node system, so that I could write deep learning software that scales for very large systems with thousands of servers – that would not be possible to study with a single machine.

Andrew M. Farrell says

What reading materials would you recommend for basic reading and what would you recommend for working through to get a start in deep learning?

timdettmers says

Andrew, that is a question I was asked again and again and I think I will write a dedicated blog post for this topic. To give good advice for what to read and how to proceed towards understanding and application of deep learning one needs to know a persons background (computer science, math, other science, business, etc.) and goals (mere knowledge, application in industry, application on common machine learning tasks, doing research in deep learning, etc.).

Generally however, one can get started quite easily by first going through this cousera course followed by a read through the deeplearning.net literature.

This path is particular helpful if you are trying to understand deep learning and aim for doing deep learning research. If you want to merely apply deep learning, this path is too unpractical and one needs to choose a different path. I will try to get an blog post online which clarifies these other paths.

EagleFlyFree says

Hi Tim, what about the practical approach? I am CS and Math major, have taken Andrew Ng’s course and mining massive datasets. Also trying to study Hinton’s course. But what next?

Tim Dettmers says

This is a good question and I think about writing a blog post about it, but because I am a bit short of time right now, I think that blog post would be only happen in a month or so — so I give you a short answer here.

It all depends what you want to do and what you exactly mean with practical. When you study deep learning in a research setting it can also be highly practical, but I assume that you mean practical in the sense of using deep learning for practical projects in industry. If this is so then I would go along these steps:

Pure deep learning:

1\. Read some practical guides on training deep learning

2\. Work on some past deep learning Kaggle competitions and figure it out, how to get a okay score (its perfectly alright if you do not score well at this point)

3\. Read Kaggle forums and blog posts about the winning deep learning solutions in these deep learning competitions

4\. Try to imitate (3.) and do it as long as you need to score well on past competitions (top 20 or so)

5\. Get new data sets where established benchmarks exists, go from small data sets to large ones (CIFAR -> ? -> ImageNet -> ?), try to score well

6\. Read academic papers of state of the art solutions and repeat (5.)

Machine Learning + deep learning

1\. Read winning Kaggle forum posts of past Kaggle competitions

2\. Play around in competitions, try to apply everything that you read (these competitions can be old or new)

3\. Do again (1.) and (2.) a few times (maximum of 2-3 times)

4\. Enter new competitions and try to score well; try to focus on one competition at a time and do well there

5\. Collaborate with other competitors that are better than you are and learn from them

Both approaches should take you about 2-4 years if you work everyday for a bit. It is a though journey, but if you persist you should be an expert in practical application by the end of this.

edude03 says

Sorry if this was answered elsewhere but why did you opt for multiple systems over 1 systems with 4 GPUs or using multi GPU cards like FASTRA II?

timdettmers says

I wanted to the test the performance of GPU clusters that is why I build a 3 + 1 GPU cluster. A 4 GPU system is definitely faster than a 3 GPU + 1 GPU cluster. However, a system like FASTRA II is slower than a 4 GPU system for deep learning. This is mainly because a single CPU just supports 40 PCIe lanes, i.e. 16/8/8/8 or 16/16/8 for 4 or 3 GPUs. Adding more GPUs, if supported, will slow down the speed you can transfer between PCIe lanes. Also a dual-GPU has an interconnect that is similar to PCIe, thus there is no big increase in speed because synchronization needs to run over the same PCIe lanes (it actually might be much slower). Using 4 fast GPUs will be faster than 13 slow GPUs. This is different from many use-cases in high performance computing, where pure bandwidth is less important and sheer computing power reigns supreme (the bottleneck is still the bandwidth, but much less so). Here the FASTRA II will be quite powerful, but not for deep learning.

dh says

can you please explain more about your cluster setup? i’m trying to build a 2-node cluster too.

1\. did you have to setup a head node to manage the 2 compute nodes? if so, what is the hardware + software for the head node?

2\. how do your 2 nodes communicate with each other? is that just through an ethernet cable?

thanks,

dh

Tim Dettmers says

1\. No head node required

2\. I used 2 infiniband cards with infiniband cable; they communicate via the infiniband protocol

Normal ethernet will be way too slow, you will need speeds > 40 Gbit/s (5 GB/s), favorably FDR (56 Gbits/s, reliable) or even the new EDR (100 Gbits/s, expensive and nobody knows how reliable).

MM says

40GigE is readily available and in moderately wide use. Cost per port is comparable with IB. 100GigE is also available and in use in a handful of companies, albeit only from Mellanox and as costly as one might expect.

James Hill says

Great Post!

dh says

re: ethernet bandwidth. do you really need that fast of a connection? most of the computation is done on individual nodes and only the message passing is done between nodes. what kind of data do you send from one node to another? why do you need that fast of a connection?

re: head node. is there any advantage of setting up a head node (for deep learning)? it looks like most cluster architecture comes with a head node.

thanks!

Tim Dettmers says

You may want to read my other blog posts about parallelism. Those blog posts contain in depth explanations of the parallelism bottlenecks and show that the largest bottleneck is the network connection. A GPU clusters with two nodes with a 1 GBit/s connection will probably run slower than a single computer for almost any deep learning application.

A short calculation for MNIST: 1 Gbit/s is 31 MB/s for each GPU. A 1200×1200 matrix is about 5 MB. So you can synchronize 6 split MNIST batches per second. A single GPU operates at about 150 batches per second on MNIST for a batch size of 128. A GPU cluster will thus be about 25 times slower than a single GPU on this task if you use 1Gbit/s ethernet. Of course the numbers are better if you alter the batch size, but it will still be slower on MNIST. This is better for convolutional nets, but not much better. A fast connection is just mandatory.

There is no computational advantage in having a dedicated head node for a two computer cluster, but if you have a few dozen computers it might be better to abstract the access to the cluster for organizational and security reasons.

DeepLearning\_Man says

Hi Tim ,

i building an 8 x Nvidia GTX Titan X GPU box for my Research in Deep learning for Algo trading but i decided to change it a bit to 4 x Nvidia GTX Titan X plus 4 x Nvidia GTX Z in order to accomodate some mathematical calculations using Double precision. Should stick with my original plan or change it ?

Tim Dettmers says

Double precision is good if you need to solve differential equations which may arise in economics; other than that double precision has little advantage (no advantage for deep learning).

Be aware that GPUs of different chipsets cannot communicate via GPU buffers with each other (for a mix of Z + X you need to GPU->CPU->GPU for communication; for 8x X you can use instead GPU->GPU).

Other than that, it is quite difficult to utilize all the cards for a single algorithm (I write good software for that at the moment, but it will take some weeks until it reaches a solid state). If you run one algorithm on each GPU, the GTX Titan X will be better than the GTX Titan Z. Please also remember, that the GTX Titan Z has a width of 3 slots instead of 2, so if you want to fit 4 cards next to each other you need to buy the water cooled variant (which has a reduced width of the normal 2 slots).

Personally, if double precision is not needed, I would definitely go for the 8x GTX Titan X. If you are very serious about differential equations you might also want to look at Tesla cards: Their memory correction modules are very helpful for precise numerical approximation to differential equations.

Hope this helps — good luck with your system!

DeepLearning\_Man says

Thanks Tim, I am planning to do Deep Learning research in high frequency trading , Low latency algo trading and medium latency algo trading in forex trading. I am using TYAN FT77CB7079 (B7079F77CV10HR) which allows for 8 Dual size GPUs such as Titan Z and Tesla K80. Some of the Algorithms might involve various algos involving Linear Algebra and computational calculus. Since i have 2 Xeon CPUs E5-2660 V3 each with 40 PCI-E x16 lanes. I plan to use 4 Titan X and 4 x Titan Z and try to split my workload between the two groups of GPUs.

Tim Dettmers says

This sounds like a solid system. Using 4 Titan Z efficiently is challenging, but for double precision these GPUs will be very valuable (computational calculus).

DeepLearning\_Man says

Hi Tim,

Since it is quite difficult to utilize all the cards for a single algorithm. Do you have the software for that , which your were writing, i can be your tester if you don’t mind. I can also contribute to the development of the software. What programming language are you using for this software?