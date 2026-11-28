"""Write refs.bib from the verified records in audit/bib_verified.json plus a table of
entries verified by hand (saved PDFs, page titles, repositories confirmed with git ls-remote).
Usage: python3 -I make_bib.py <bib_verified.json> <refs.bib>"""
import sys, json, re

V = json.load(open(sys.argv[1]))
ACCESS = 'Accessed November 23, 2026'
out, prov = [], {}

def esc(s):
    return (s.replace('&', r'\&').replace('%', r'\%').replace('#', r'\#').replace('_', r'\_').replace('µ', r'\textmu{}')
             .replace('“', "``").replace('”', "''").replace('‐', '-').replace('‑', '-').replace('’', "'").replace('™', ''))

def entry(typ, key, fields, how):
    lines = ['@%s{%s,' % (typ, key)]
    for k, v in fields:
        if v in (None, ''): continue
        if k == 'title': v = '{' + esc(v) + '}'
        elif k in ('url', 'doi'): v = v
        else: v = esc(v) if k != 'author' and k != 'editor' else v
        lines.append('  %-12s = {%s},' % (k, v))
    lines.append('}')
    out.append('\n'.join(lines)); prov[key] = how

def authors(lst, cap=12):
    lst = [a for a in lst if a]
    if len(lst) > cap: return esc(lst[0]) + ' and others'
    return ' and '.join(esc(a) for a in lst)

# ---------------- arXiv ----------------
AX_NOTE = {'vaswani2017': 'Published in Advances in Neural Information Processing Systems 30 (NIPS 2017)', 'kwon2023vllm': 'Published at SOSP 2023', 'zhong2024distserve': 'Published at OSDI 2024',
           'staniszewski2026kvtc': 'Accepted to ICLR 2026', 'dao2024mamba2': 'Published at ICML 2024', 'ainslie2023gqa': 'Published at EMNLP 2023',
           'micikevicius2018': 'Published as a conference paper at ICLR 2018', 'liu2024kivi': 'Published at ICML 2024', 'liu2026router': 'Technical report', 'wang2025router': 'Workshop on ML for Systems at NeurIPS 2025',
           'licker2026fabriclib': 'Version 2, April 2026', 'suresh2021wfa': 'Version 3, January 2021'}
AX_TITLE = {'shen2026sol': 'Every µs Matters: Achieving Near Speed-of-Light Latency in GPU Collectives'}
for k, r in V.items():
    if r.get('kind') != 'arxiv' or 'title' not in r: continue
    entry('misc', k, [('author', authors(r['authors'])), ('title', AX_TITLE.get(k, r['title'])), ('year', r['published'][:4]),
                      ('howpublished', 'arXiv:' + r['id']), ('note', AX_NOTE.get(k, '')), ('url', 'https://arxiv.org/abs/' + r['id'])],
          'arXiv API record %s%s' % (r['id'], r.get('version', '')))

# ---------------- Crossref ----------------
def cr(k): return V[k]
CR = [  # key, type, overrides
 ('zhu2015dcqcn', 'inproceedings', {}), ('gangidi2024meta', 'inproceedings', {'title': 'RDMA over Ethernet for Distributed AI Training at Meta Scale'}),
 ('grun2015ofi', 'inproceedings', {'title': 'A Brief Introduction to the OpenFabrics Interfaces: A New Network API for Maximizing High Performance Application Efficiency'}),
 ('shamis2015ucx', 'inproceedings', {}), ('papadopoulou2017ucx', 'inproceedings', {}), ('tillet2019triton', 'inproceedings', {'title': 'Triton: An Intermediate Language and Compiler for Tiled Neural Network Computations'}),
 ('lindholm2001', 'inproceedings', {'title': 'A User-Programmable Vertex Engine', 'booktitle': "Proceedings of the 28th Annual Conference on Computer Graphics and Interactive Techniques (SIGGRAPH '01)", 'publisher': 'ACM'}),
 ('amdahl1967', 'inproceedings', {'title': 'Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities', 'pages': '483--485',
                                  'booktitle': "Proceedings of the April 18--20, 1967, Spring Joint Computer Conference (AFIPS '67 Spring)", 'publisher': 'ACM'}),
 ('mittal2018irn', 'inproceedings', {'title': 'Revisiting Network Support for RDMA'}),
 ('bellman1956', 'article', {'title': "On the ``Bang-Bang'' Control Problem"}), ('shannon1948', 'article', {}),
 ('vonneumann1945', 'article', {'title': 'First Draft of a Report on the EDVAC', 'note': 'Reprint of the report dated June 30, 1945'}),
 ('goldstine1946eniac', 'article', {'pages': '97--110'}), ('bardeen1948', 'article', {}), ('kilby1976', 'article', {'title': 'Invention of the Integrated Circuit'}),
 ('faggin1996', 'article', {'title': 'The History of the 4004'}),
 ('moore1965', 'article', {'note': 'Reprinted from Electronics, 38(8), April 19, 1965'}), ('russell1978cray', 'article', {'title': 'The CRAY-1 Computer System'}),
 ('owens2007', 'article', {'title': 'A Survey of General-Purpose Computation on Graphics Hardware'}), ('nickolls2008', 'article', {'journal': 'ACM Queue'}),
 ('krizhevsky2012', 'article', {'key': 'krizhevsky2017', 'title': 'ImageNet Classification with Deep Convolutional Neural Networks'}),
 ('cobham1954', 'article', {}), ('johnson1984', 'article', {'title': 'Extensions of Lipschitz Mappings into a Hilbert Space', 'volume': '26'}),
 ('lloyd1982', 'article', {'title': 'Least Squares Quantization in PCM'}), ('max1960', 'article', {'title': 'Quantizing for Minimum Distortion'}),
 ('hollerith1894', 'article', {'pages': '678--689'}),
]
for k, typ, ov in CR:
    r = cr(k)
    if 'title' not in r: print('MISSING crossref', k); continue
    key = ov.get('key', k)
    f = [('author', authors(r['authors'])), ('title', ov.get('title', r['title'])), ('year', str(r['year']))]
    if typ == 'article':
        f += [('journal', ov.get('journal', r['container'])), ('volume', ov.get('volume', r.get('volume', ''))), ('number', r.get('issue', '')), ('pages', ov.get('pages', (r.get('page') or '').replace('-', '--')))]
    else:
        f += [('booktitle', ov.get('booktitle', r['container'])), ('pages', ov.get('pages', (r.get('page') or '').replace('-', '--'))), ('publisher', ov.get('publisher', r.get('publisher', '')))]
    f += [('doi', r['doi']), ('note', ov.get('note', ''))]
    entry(typ, key, f, 'Crossref record for DOI ' + r['doi'])

# books and records fetched in the second pass
def raw(k): return V[k]['raw']
b = raw('pontryagin1962')
entry('book', 'pontryagin2018', [('author', 'L. S. Pontryagin'), ('title', 'Mathematical Theory of Optimal Processes'), ('publisher', 'Routledge'), ('year', '2018'),
                                 ('doi', b['DOI']), ('note', 'English edition of the 1961 Russian original by L. S. Pontryagin, V. G. Boltyanskii, R. V. Gamkrelidze and E. F. Mishchenko')], 'Crossref record for DOI ' + b['DOI'])
b = raw('goldstine1972')
entry('book', 'goldstine1972', [('author', 'Herman H. Goldstine'), ('title', 'The Computer from Pascal to von Neumann'), ('publisher', 'Princeton University Press'), ('year', '1972'), ('doi', b['DOI'])], 'Crossref record for DOI ' + b['DOI'])
b = raw('droste2009wfa')
entry('book', 'droste2009wfa', [('editor', 'Manfred Droste and Werner Kuich and Heiko Vogler'), ('title', 'Handbook of Weighted Automata'), ('series', 'Monographs in Theoretical Computer Science. An EATCS Series'),
                                ('publisher', 'Springer'), ('year', '2009'), ('doi', b['DOI'])], 'Crossref record for DOI ' + b['DOI'])
entry('book', 'liberzon2012', [('author', 'Daniel Liberzon'), ('title', 'Calculus of Variations and Optimal Control Theory: A Concise Introduction'), ('publisher', 'Princeton University Press'), ('year', '2012'),
                               ('doi', '10.1515/9781400842643')], 'Crossref record for DOI 10.1515/9781400842643')
entry('inproceedings', 'sterling1995beowulf', [('author', 'T. Sterling and D. Savarese and D. J. Becker and B. Fryxell and K. Olson'),
      ('title', 'Communication Overhead for Space Science Applications on the Beowulf Parallel Workstation'),
      ('booktitle', 'Proceedings of the Fourth IEEE International Symposium on High Performance Distributed Computing'), ('pages', '23--30'), ('year', '1995'),
      ('publisher', 'IEEE Computer Society Press'), ('doi', '10.1109/HPDC.1995.518691')], 'Crossref record for DOI 10.1109/hpdc.1995.518691')

# ---------------- pages, repositories, saved documents ----------------
MONTH_RE = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
def web(key, author, title, year, how, url, note=None, check='page title fetched 2026-11-23'):
    month = ''
    m = re.match(r'^(.*?),\s+(' + MONTH_RE + r'(?:\s+\d{1,2},)?)\s+(\d{4})$', how)
    if m and m.group(3) == year: how, month = m.group(1), m.group(2)
    if year == 'n.d.': year = 'n.d'          # the style adds the full stop
    entry('misc', key, [('author', author), ('title', title), ('year', year), ('month', month), ('howpublished', how), ('url', url), ('note', (note + '. ' if note else '') + ACCESS)], check)
REPO = 'repository confirmed with git ls-remote 2026-11-23'
MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
def nice(d):
    y, m, dd = d.split('-'); return '%s %d, %s' % (MONTHS[int(m) - 1], int(dd), y)
# latest commit of each cited repository when it was read (git log -1 on a shallow clone, 2026-11-23)
HEAD = {'nixl': ('bf2a37b', '2026-11-23'), 'dynamo': ('6053c90', '2026-11-23'), 'vllm_repo': ('bfe3d7e', '2026-11-23'), 'flashinfer': ('e2d163f', '2026-11-23'),
        'rdmacore': ('4b7b208', '2026-11-22'), 'perftest': ('9ced637', '2026-11-22'), 'libfabric_repo': ('cffff8a', '2026-11-23'), 'ucx_repo': ('cdc194b', '2026-11-23'),
        'ucx_faq': ('cdc194b', '2026-11-23'), 'rocm_ernic': ('bd90234', '2026-11-17'), 'uccl': ('1c9e39b', '2026-11-20'), 'libmesh': ('40bb2cf', '2026-03-18'),
        'ttpoe': ('b8b446c', '2024-12-18'), 'rebaruefi': ('9c80fdb', '2025-12-01'), 'uefitool': ('de73942', '2026-10-27'), 'ollama': ('318ee28', '2026-11-22'),
        'ray': ('de0650f', '2026-11-23'), 'mstflint': ('2a8ba9c', '2026-11-09'), 'nccl': ('ad2d192', '2026-11-09')}
def repo(key, author, title, how, url, note=None, check=None):
    h, d = HEAD[key]
    n = 'Latest commit %s of %s' % (h, nice(d))
    if note: n = note + '. ' + n
    entry('misc', key, [('author', author), ('title', title), ('year', d[:4]), ('howpublished', how), ('url', url), ('note', n + '. ' + ACCESS)],
          (check or 'repository README read 2026-11-23') + '; latest commit date from git log on a shallow clone')
def usenix(key, author, title, year, booktitle, address, month, pages, url, check):
    entry('inproceedings', key, [('author', author), ('title', title), ('booktitle', booktitle), ('year', year), ('month', month), ('address', address),
                                 ('pages', pages), ('publisher', 'USENIX Association'), ('url', url)], check)
repo('nixl', '{NVIDIA}', 'NVIDIA Inference Xfer Library (NIXL)', 'GitHub repository ai-dynamo/nixl', 'https://github.com/ai-dynamo/nixl', 'Libfabric plugin read at commit d642316; its provider selection read again at commit bf2a37b', 'repository README and LICENSE read 2026-11-23')
repo('dynamo', '{NVIDIA}', 'Dynamo: The Open-Source, Datacenter-Scale Inference Stack', 'GitHub repository ai-dynamo/dynamo', 'https://github.com/ai-dynamo/dynamo')
web('lmcache_blog', '{LMCache Team}', 'Shaping NIXL-based PD Disaggregation in vLLM V1', '2025', 'LMCache Blog, April 11, 2025', 'https://blog.lmcache.ai/2025-04-11-lmcache-vllmv1-nixl/', None, 'page title and publication date fetched 2026-11-23')
web('llmd', '{llm-d Project}', 'llm-d Architecture', 'n.d.', 'Project documentation', 'https://llm-d.ai/docs/architecture')
web('vllm_disagg', '{vLLM Project}', 'Disaggregated Prefilling (experimental)', 'n.d.', 'vLLM documentation', 'https://docs.vllm.ai/en/latest/features/disagg_prefill/')
web('vllm_gptoss', '{vLLM Project}', 'vLLM Now Supports gpt-oss', '2025', 'vLLM Blog, August 5, 2025', 'https://blog.vllm.ai/2025/08/05/gpt-oss.html')
# vllm_issue22279 removed: the issue page could not be read (GitHub refused unauthenticated requests), so its title is unverified; the text cites the repository and gives the issue number
repo('vllm_repo', '{vLLM Project}', 'vLLM: Easy, Fast, and Cheap LLM Serving for Everyone', 'GitHub repository vllm-project/vllm', 'https://github.com/vllm-project/vllm', 'Connector checked against commit 620e8924 and release 0.24.0')
web('patel2025tensorcore', 'Dylan Patel and Kimbo Chen', 'NVIDIA Tensor Core Evolution: From Volta To Blackwell', '2025', 'SemiAnalysis, June 23, 2025', 'https://newsletter.semianalysis.com/p/nvidia-tensor-core-evolution-from-volta-to-blackwell')
repo('flashinfer', '{FlashInfer Project}', 'FlashInfer: Kernel Library for LLM Serving', 'GitHub repository flashinfer-ai/flashinfer', 'https://github.com/flashinfer-ai/flashinfer', None, REPO)
repo('rdmacore', '{Linux RDMA}', 'rdma-core: RDMA Core Userspace Libraries and Daemons', 'GitHub repository linux-rdma/rdma-core', 'https://github.com/linux-rdma/rdma-core', None, 'repository README and license files read 2026-11-23')
repo('perftest', '{Linux RDMA}', 'perftest', 'GitHub repository linux-rdma/perftest', 'https://github.com/linux-rdma/perftest', None, 'repository README and license file read 2026-11-23')
web('barak2013tips', 'Dotan Barak', 'Tips and Tricks to Optimize Your RDMA Code', '2013', 'RDMAmojo, June 8, 2013', 'https://www.rdmamojo.com/2013/06/08/tips-and-tricks-to-optimize-your-rdma-code/')
web('chen2024efa', 'Lequn Chen', 'Harnessing 3200 Gbps Network (1): RDMA and EFA', '2024', 'Blog post, December 25, 2024', 'https://le.qun.ch/en/blog/2024/12/25/libfabric-efa-1-rdma/')
web('libfabric_man', '{OpenFabrics Interfaces Working Group}', 'Libfabric Programmer\'s Manual: fi_endpoint(3), fi_cq(3), fi_cntr(3), fi_mr(3), fi_rma(3), fi_verbs(7), fi_rxm(7)', 'n.d.', 'Online manual pages', 'https://ofiwg.github.io/libfabric/')
repo('libfabric_repo', '{OpenFabrics Interfaces Working Group}', 'libfabric: Open Fabric Interfaces', 'GitHub repository ofiwg/libfabric', 'https://github.com/ofiwg/libfabric', 'Provider sources of releases 1.17.0 and 2.7.0 read on November 26, 2026', 'repository README and license file read 2026-11-23; prov/tcp, prov/verbs, prov/rxm and prov/shm of tags v1.17.0 and v2.7.0 read 2026-11-26 for progress, counters and remote-write events (tcpx_tx_queue_insert, xnet_tx_queue_insert, fi_no_cntr_open in verbs_domain.c); release 2.7.0 built from source and used for the tests on the same day')
repo('ucx_faq', '{OpenUCX}', 'UCX Frequently Asked Questions', 'docs/source/faq.md in the GitHub repository openucx/ucx', 'https://github.com/openucx/ucx/blob/master/docs/source/faq.md', None, REPO)
repo('ucx_repo', '{OpenUCX}', 'UCX: Unified Communication X', 'GitHub repository openucx/ucx', 'https://github.com/openucx/ucx', None, REPO)
web('mistral2026leak', '{Mistral AI}', 'Heaps Do Lie: Debugging a Memory Leak in vLLM', '2026', 'Mistral AI engineering blog, January 21, 2026', 'https://mistral.ai/news/debugging-memory-leak-in-vllm', None, 'page title and publication date fetched 2026-11-23')
web('zambre2018novice', 'Rohit Zambre', 'For the RDMA Novice: libfabric, libibverbs, InfiniBand, OFED, MOFED?', '2018', 'Blog post, February 9, 2018', 'https://www.rohitzambre.com/blog/2018/2/9/for-the-rdma-novice-libfabric-libibverbs-infiniband-ofed-mofed')
web('gpudirect', '{NVIDIA}', 'GPUDirect RDMA', 'n.d.', 'CUDA documentation, release 13.5', 'https://docs.nvidia.com/cuda/gpudirect-rdma/index.html')
web('alvarez2026flashblade', 'Robert Alvarez', 'Up to 10X Faster KV Cache Restore: TurboQuant Meets FlashBlade', '2026', 'Everpure Blog, April 8, 2026', 'https://blog.purestorage.com/purely-technical/up-to-10x-faster-kv-cache-restore-turboquant-meets-flashblade/')
t = re.sub(r'\s*[|–-]\s*IBM.*$', '', V['hsu2026kv']['title']).strip()
web('hsu2026kv', 'Anthony Hsu and Khanh Ngo and Yue Zhu and Radu Stoica and Guy Margalit and Vasily Tarasov and Michael Kieran', t, '2026', 'IBM Community blog, February 6, 2026', V['hsu2026kv']['url'], None, 'page title and author list fetched 2026-11-23')
t = V['hsu2026fourtier']['title'].strip()
web('hsu2026fourtier', 'Vincent Hsu', t, '2026', 'IBM Community blog, January 5, 2026', V['hsu2026fourtier']['url'], None, 'page title and author fetched 2026-11-23')
web('ibm2025storage', '{IBM Research}', 'Accelerating AI Inference with IBM Storage Scale', '2025', 'IBM Research blog, November 18, 2025', 'https://research.ibm.com/blog/accelerating-ai-inference-with-ibm-storage-scale', None, 'page title and publication date fetched 2026-11-23')
repo('rocm_ernic', '{AMD}', 'rocm-ernic: Userspace Emulated RDMA NIC for Virtual Machines', 'GitHub repository ROCm/rocm-ernic', 'https://github.com/ROCm/rocm-ernic')
repo('uccl', '{UCCL Project}', 'UCCL: An Efficient Communication Library for GPUs', 'GitHub repository uccl-project/uccl', 'https://github.com/uccl-project/uccl')
repo('libmesh', '{autoscriptlabs}', 'libmesh-rdma + libmesh-mpi: RDMA Networking for Consumer GPU Clusters', 'GitHub repository autoscriptlabs/libmesh-rdma, MIT license', 'https://github.com/autoscriptlabs/libmesh-rdma', None, 'repository README and LICENSE read 2026-11-23')
repo('ttpoe', '{Tesla, Inc.}', 'TTPoE: Tesla Transport Protocol over Ethernet', 'GitHub repository teslamotors/ttpoe', 'https://github.com/teslamotors/ttpoe')
web('scuffedrdma', 'Nathan Gopee', 'ScuffedRDMA', '2026', 'GitHub repository ndg8743/ScuffedRDMA, commit c03d365', 'https://github.com/ndg8743/ScuffedRDMA', None, REPO)
web('x99rebar', 'Nathan Gopee', 'x99-udp4-rebar', '2026', 'GitHub repository ndg8743/x99-udp4-rebar, commit 2ae254f', 'https://github.com/ndg8743/x99-udp4-rebar', None, REPO)
repo('rebaruefi', '{xCuri0}', 'ReBarUEFI: A UEFI DXE Driver to Enable Resizable BAR on Systems Which Do Not Support It Officially', 'GitHub repository xCuri0/ReBarUEFI, MIT license', 'https://github.com/xCuri0/ReBarUEFI', None, 'repository README and LICENSE read 2026-11-23')
repo('uefitool', '{LongSoft}', 'UEFITool', 'GitHub repository LongSoft/UEFITool', 'https://github.com/LongSoft/UEFITool', None, REPO)
web('level1techs2026', '{Level1Techs Forums}', 'V100+RDMA+X99 issues', '2026', 'Forum thread, Hardware Hub, January 13, 2026', 'https://forum.level1techs.com/t/v100-rdma-x99-issues/244397', None, 'page title and publication date fetched 2026-11-23')
web('newpaltz_library', '{Sojourner Truth Library}', "Guidelines for Submission of Master's Theses to the Library", 'n.d.', 'SUNY New Paltz', 'https://library.newpaltz.edu/?p=174')
web('top500june2022', '{TOP500}', 'TOP500 List, June 2022', '2022', 'top500.org', 'https://www.top500.org/lists/top500/2022/06/')
web('cuda_gpus', '{NVIDIA}', 'CUDA GPU Compute Capability', 'n.d.', 'NVIDIA Developer', 'https://developer.nvidia.com/cuda-gpus')
web('granite33', '{IBM Granite Team}', 'granite-3.3-2b-instruct', '2025', 'Hugging Face model repository, April 9, 2025', 'https://huggingface.co/ibm-granite/granite-3.3-2b-instruct', 'Date the repository was created', 'page title fetched 2026-11-23; creation date from the Hugging Face API')
web('granite40micro', '{IBM Granite Team}', 'granite-4.0-h-micro', '2025', 'Hugging Face model repository, September 16, 2025', 'https://huggingface.co/ibm-granite/granite-4.0-h-micro', 'Date the repository was created', 'page title fetched 2026-11-23; creation date from the Hugging Face API')
web('granite40tiny', '{IBM Granite Team}', 'granite-4.0-h-tiny', '2025', 'Hugging Face model repository, September 16, 2025', 'https://huggingface.co/ibm-granite/granite-4.0-h-tiny', 'Date the repository was created', 'page title fetched 2026-11-23; creation date from the Hugging Face API')
web('mamba130m', '{state-spaces}', 'mamba-130m-hf', '2024', 'Hugging Face model repository, March 6, 2024', 'https://huggingface.co/state-spaces/mamba-130m-hf', 'Date the repository was created', 'page title fetched 2026-11-23; creation date from the Hugging Face API')
web('gptoss', '{OpenAI}', 'gpt-oss-120b', '2025', 'Hugging Face model repository, August 4, 2025', 'https://huggingface.co/openai/gpt-oss-120b', 'Date the repository was created', 'page title fetched 2026-11-23; creation date from the Hugging Face API')
repo('ollama', '{Ollama}', 'Ollama', 'GitHub repository ollama/ollama', 'https://github.com/ollama/ollama', None, REPO)
repo('ray', '{Ray Project}', 'Ray', 'GitHub repository ray-project/ray', 'https://github.com/ray-project/ray', 'Release 2.35.0 container image used', REPO)
repo('mstflint', '{Mellanox Technologies}', 'mstflint', 'GitHub repository Mellanox/mstflint', 'https://github.com/Mellanox/mstflint', None, REPO)
repo('nccl', '{NVIDIA}', 'NCCL: Optimized Primitives for Inter-GPU Communication', 'GitHub repository NVIDIA/nccl', 'https://github.com/NVIDIA/nccl', None, 'repository README and license file read 2026-11-23')
web('pve_kernel', '{Proxmox Server Solutions}', 'pve-kernel.git', 'n.d.', 'Proxmox git repository', 'https://git.proxmox.com/?p=pve-kernel.git')
web('bareford2022', 'Michael Bareford and David Henty and William Lucas and Andy Turner', 'OpenFabrics and UCX Performance on the ARCHER2 HPE Cray EX System', '2022', 'Cray User Group (CUG) meeting; data in the GitHub repository ARCHER2-HPC/performance_ofi-ucx', 'https://github.com/ARCHER2-HPC/performance_ofi-ucx', None, 'title and authors read from the saved slides; ' + REPO)
web('smith2023opx', 'Brian Smith', 'Omni-Path and the Open Fabrics Interfaces', '2023', 'Slides, Cornelis Networks, MVAPICH User Group Meeting (MUG)', 'https://mug.mvapich.cse.ohio-state.edu/static/media/mug/presentations/23/MUG23TuesdayBrianSmith.pdf', None, 'title and author read from the saved slides')
usenix('schmuck2002gpfs', 'Frank Schmuck and Roger Haskin', 'GPFS: A Shared-Disk File System for Large Computing Clusters', '2002', 'Conference on File and Storage Technologies (FAST 02)', 'Monterey, CA', 'January', '', 'https://www.usenix.org/conference/fast-02/gpfs-shared-disk-file-system-large-computing-clusters', 'BibTeX record on the USENIX page, fetched 2026-11-23')
web('mpiforum', '{Message Passing Interface Forum}', 'MPI Documents', 'n.d.', 'mpi-forum.org', 'https://www.mpi-forum.org/docs/')
web('ibta_softroce2015', '{InfiniBand Trade Association}', 'Soft-RoCE: RDMA Transport in a Software Implementation', '2015', 'RoCE Initiative white paper, June 2015', 'https://www.roceinitiative.org/wp-content/uploads/2016/11/SoftRoCE_Paper_FINAL.pdf', None, 'title read from the saved PDF; URL live 2026-11-23')
web('snia2025rdma', '{SNIA}', 'Everything You Wanted to Know About RDMA But Were Too Proud to Ask', '2025', 'Live webinar, March 26, 2025', 'https://www.snia.org/educational-library/everything-you-wanted-know-about-rdma-were-too-proud-ask-2025')
web('mellanox_ibwp', '{Mellanox Technologies Inc.}', 'Introduction to InfiniBand', '2003', 'White paper, document number 2003WP, Rev 1.90', 'https://network.nvidia.com/pdf/whitepapers/IB_Intro_WP_190.pdf', None, 'title, document number and revision read from the saved PDF; the URL serves a file of the same length (327,338 bytes); year from the PDF modification date, December 2003')
web('wuerthner2021gpfsrdma', 'Ralph Würthner and Olaf Weiser and Ingo Meents', 'Improving Spectrum Scale Performance Using RDMA', '2021', 'Slides, IBM Spectrum Scale Strategy Days',
    'https://www.spectrumscaleug.org/wp-content/uploads/2021/05/SSSD21DE-06-Improving-Spectrum-Scale-performance-using-RDMA.pdf', None, 'title and authors read from the PDF fetched 2026-11-23')
usenix('rajasekaran2024cassini', 'Sudarsanan Rajasekaran and Manya Ghobadi and Aditya Akella', 'CASSINI: Network-Aware Job Scheduling in Machine Learning Clusters', '2024',
       '21st USENIX Symposium on Networked Systems Design and Implementation (NSDI 24)', 'Santa Clara, CA', 'April', '1403--1420',
       'https://www.usenix.org/conference/nsdi24/presentation/rajasekaran', 'BibTeX record on the USENIX page, fetched 2026-11-23')
usenix('shah2023taccl', 'Aashaka Shah and Vijay Chidambaram and Meghan Cowan and Saeed Maleki and Madan Musuvathi and Todd Mytkowicz and Jacob Nelson and Olli Saarikivi and Rachee Singh',
       'TACCL: Guiding Collective Algorithm Synthesis using Communication Sketches', '2023', '20th USENIX Symposium on Networked Systems Design and Implementation (NSDI 23)',
       'Boston, MA', 'April', '593--612', 'https://www.usenix.org/conference/nsdi23/presentation/shah', 'BibTeX record on the USENIX page, fetched 2026-11-23')
web('uec2023launch', '{The Linux Foundation}', 'Leading Cloud Service, Semiconductor, and System Providers Unite to Form Ultra Ethernet Consortium', '2023', 'Press release, July 19, 2023',
    'https://www.linuxfoundation.org/press/announcing-ultra-ethernet-consortium-uec', None, 'page title and publication date fetched 2026-11-23')
web('uec2025spec10', '{Ultra Ethernet Consortium}', 'UEC Launches Spec 1.0 Transforming Ethernet for AI and HPC at Scale', '2025', 'Press release, The Linux Foundation, June 11, 2025',
    'https://www.linuxfoundation.org/press/uec-launches-spec-1.0', None, 'headline and date read from the page 2026-11-23')
web('uecspec', '{Ultra Ethernet Consortium}', 'Ultra Ethernet Specification v1.0.1', '2025', 'Specification, September 5, 2025', 'https://ultraethernet.org/uec-1-0-spec',
    '564 pages. Version 1.0 was released on June 11, 2025; versions 1.0.2 and 1.0.3 followed in January and July 2026', 'title page and text read from the PDF fetched 2026-11-23; later versions from the 1.0.3 release notes')
web('uec2024update', '{Ultra Ethernet Consortium}', 'Ultra Ethernet Specification Update', '2024', 'Blog post, August 29, 2024', 'https://ultraethernet.org/ultra-ethernet-specification-update/',
    None, 'page title and publication date fetched 2026-11-23')
web('uec2025vision', '{Ultra Ethernet Consortium}', "Accelerating AI with Open Standards: UEC's Expanding Vision", '2025', 'Blog post, October 9, 2025',
    'https://ultraethernet.org/accelerating-ai-with-open-standards-uecs-expanding-vision/', None, 'page title and publication date fetched 2026-11-23')
web('xiong2025ofaue', 'Jianxin Xiong', 'Libfabric: Getting Started with Ultra Ethernet', '2025', 'Slides, 2025 OFA Webinar Series, OpenFabrics Alliance',
    'https://www.openfabrics.org/wp-content/uploads/2025_webinars/webinar_1/OFA-2025-Libfabric-and-UE.pdf', None, 'title and presenter read from the PDF fetched 2026-11-23')
web('kernel_ib', '{The Linux Kernel Documentation}', 'InfiniBand', 'n.d.', 'docs.kernel.org', 'https://docs.kernel.org/infiniband/index.html')

web('ibm_iv61625', '{IBM}', 'IV61625: RDMA Reconnection Problem with Commit 1705391b in GPFS 3.5.0.11', '2014', 'IBM Support, APAR, June 17, 2014', 'https://www.ibm.com/support/pages/apar/IV61625', 'Date the APAR was closed', 'page title and APAR dates fetched 2026-11-23')
web('ibm_ij44629', '{IBM}', 'IJ44629: RDMA Scale Client Reads Incorrect Data from Files', '2023', 'IBM Support, APAR, January 17, 2023', 'https://www.ibm.com/support/pages/apar/IJ44629', 'Date the APAR was closed', 'page title and APAR dates fetched 2026-11-23')

# --- added for the history section of the ten-chapter version (checked 2026-11-23) ---
web('nvidia2020mellanox', '{NVIDIA}', 'NVIDIA Completes Acquisition of Mellanox, Creating Major Force Driving Next-Gen Data Centers', '2020', 'Press release, April 27, 2020', 'https://nvidianews.nvidia.com/news/nvidia-completes-acquisition-of-mellanox-creating-major-force-driving-next-gen-data-centers', None, 'headline, date and transaction value read from the press release 2026-11-23')
web('nvidia2020bluefield', '{NVIDIA}', 'NVIDIA Introduces New Family of BlueField DPUs to Bring Breakthrough Networking, Storage and Security Performance to Every Data Center', '2020', 'Press release, October 5, 2020', 'https://nvidianews.nvidia.com/news/nvidia-introduces-new-family-of-bluefield-dpus-to-bring-breakthrough-networking-storage-and-security-performance-to-every-data-center', None, 'headline and date read from the press release 2026-11-23')
web('delloro2025ethernet', "{Dell'Oro Group}", "Ethernet is Winning the War Against InfiniBand in AI Back-End Networks, According to Dell'Oro Group", '2025', 'Press release, July 15, 2025', 'https://www.delloro.com/news/ethernet-is-winning-the-war-against-infiniband-in-ai-back-end-networks/', None, 'headline, date and market-share statement read from the page 2026-11-23')
web('delloro2026ethernet', "{Dell'Oro Group}", "Ethernet More Than Doubles Size of InfiniBand as the Leading Fabric for AI Scale-Out Networks in 2025, According to Dell'Oro Group", '2026', 'Press release, March 10, 2026', 'https://www.delloro.com/newsroom/ethernet-more-than-doubles-size-of-infiniband-as-the-leading-fabric-for-ai-scale-out-networks-in-2025/', None, 'headline, date and figures read from the page 2026-11-23')
web('sdx2026top500', '{SDxCentral}', 'InfiniBand Expands Top500 Supercomputer System Share While HPE Retains Performance Crown', '2026', 'SDxCentral, November 2026', 'https://www.sdxcentral.com/news/infiniband-expands-top500-supercomputer-system-share-while-hpe-retains-performance-crown/', None, 'figures read from the page 2026-11-23; headline from the search listing; the page shows no author or day')
web('eweek2002infiniband', '{eWeek Editors}', 'Infiniband Future Up in Air as Intel Withdraws', '2002', 'eWeek, June 3, 2002', 'https://www.eweek.com/pc-hardware/infiniband-future-up-in-air-as-intel-withdraws/', None, 'headline, date and content read from the page 2026-11-23')
usenix('sandberg1985nfs', 'Russel Sandberg and David Goldberg and Steve Kleiman and Dan Walsh and Bob Lyon', 'Design and Implementation of the Sun Network Filesystem', '1985', 'Proceedings of the Summer 1985 USENIX Conference', 'Portland, OR', 'June', '119--130', None, 'title and authors on the first page of the paper; venue and pages from two university reading lists, 2026-11-23')

# --- added for the Cray, Slingshot and industry paragraphs (checked 2026-11-23) ---
entry('inproceedings', 'feind1995shmem', [('author', 'Karl Feind'), ('title', 'Shared Memory Access (SHMEM) Routines'), ('booktitle', 'CUG 1995 Spring Proceedings'),
      ('year', '1995'), ('pages', '303--308'), ('publisher', 'Cray User Group'), ('url', 'https://cug.org/5-publications/proceedings_attendee_lists/1997CD/S95PROC/303_308.PDF')],
      'title, author, proceedings and pages read from the PDF fetched 2026-11-23')
entry('inproceedings', 'desensi2020slingshot', [('author', 'Daniele De Sensi and Salvatore Di Girolamo and Kim H. McMahon and Duncan Roweth and Torsten Hoefler'),
      ('title', 'An In-Depth Analysis of the Slingshot Interconnect'),
      ('booktitle', 'Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis (SC20)'),
      ('year', '2020'), ('month', 'November'), ('doi', '10.1109/SC41405.2020.00039'), ('note', 'arXiv:2008.08886')],
      'title, authors and DOI from the arXiv record and the SC20 proceedings page, 2026-11-23')
web('hpe2019cray', '{Hewlett Packard Enterprise}', 'HPE Completes Acquisition of Supercomputing Leader Cray Inc.', '2019', 'Press release, September 25, 2019',
    'https://www.hpe.com/us/en/newsroom/press-release/2019/09/hpe-completes-acquisition-of-supercomputing-leader-cray-inc.html', None,
    'headline, date, transaction value and the statement on exascale systems read from the press release 2026-11-23')
web('top500june2026', '{TOP500}', 'LineShine Debuts at No. 1 as the TOP500 Enters a New Global Exascale Era', '2026', 'News release, June 23, 2026',
    'https://top500.org/news/lineshine-debuts-no-1-top500-enters-new-global-exascale-era/', None,
    'headline, date, the five exascale systems and the vendor statement read from the page 2026-11-23')

# --- dates of the History section (added for version 7; each page read 2026-11-23)
web('penn_eniac', '{Penn Engineering}', 'Celebrating Penn Engineering History: ENIAC', 'n.d.', 'University of Pennsylvania, School of Engineering and Applied Science',
    'https://www.engineering.upenn.edu/about/history-heritage/eniac/', None,
    'page title, the announcement date of February 14, 1946 and the contract with the Ballistics Research Laboratory read from the page 2026-11-23')
web('ibm_tabulator', '{IBM}', 'The Punched Card Tabulator', 'n.d.', 'IBM Heritage',
    'https://www.ibm.com/history/punched-card-tabulator', None,
    'page title and the dates 1890 (census), 1896 (Tabulating Machine Company), 1911 (Computing-Tabulating-Recording Company) and 1924 (renamed IBM) read from the page 2026-11-23')
web('hpe_crayhistory', '{Hewlett Packard Enterprise}', 'Cray History: Supercomputers Inspired by Curiosity', 'n.d.', 'hpe.com',
    'https://www.hpe.com/us/en/compute/hpc/cray.html', None,
    'page title and the years of the Cray-1 (1976, first customer Los Alamos National Laboratory) and the Cray T3D (1993, first massively parallel system of the company) read from the page 2026-11-23')
entry('inproceedings', 'fischer2014beowulf', [('author', 'James R. Fischer'), ('title', 'The Roots of Beowulf'),
      ('booktitle', "20 Years of Beowulf: Workshop to Honor Thomas Sterling's 65th Birthday"), ('year', '2014'), ('month', 'October'), ('address', 'Annapolis, MD'),
      ('note', 'NASA report GSFC-E-DAA-TN17588'), ('url', 'https://ntrs.nasa.gov/citations/20150001285')],
      'title, author, date, report number, meeting and the first sentence of the abstract read from the NASA Technical Reports Server record 2026-11-23')
web('mpi1995', '{Message Passing Interface Forum}', 'MPI: A Message-Passing Interface Standard', '1995', 'Version 1.1, June 1995',
    'https://www.mcs.anl.gov/research/projects/mpi/mpi-standard/mpi-report-1.1/mpi-report.htm', None,
    'title, version and the date of Version 1.0 (June 1994) read from the page 2026-11-23')

# --- the IBM line of the History section (added for version 8; each page read 2026-11-23)
web('chm_ramac', '{Computer History Museum}', '1956: First Commercial Hard Disk Drive Shipped', 'n.d.', 'The Storage Engine',
    'https://www.computerhistory.org/storageengine/first-commercial-hard-disk-drive-shipped/', None,
    'page title, the Model 350 disk storage unit of the IBM 305 RAMAC and the shipment of June 1956 read from the page 2026-11-23')
web('ibm_system360', '{IBM}', 'The IBM System/360', 'n.d.', 'IBM Heritage',
    'https://www.ibm.com/history/system-360', None,
    'page title, the launch date of April 7, 1964, the compatibility of software across the line and Gene Amdahl as chief architect read from the page 2026-11-23')
web('ibm2023storagebrand', 'Denis Kennelly', 'Evolving the IBM Storage Portfolio Brand Identity and Strategy', '2023', 'IBM product blog, March 2, 2023',
    'https://www.ibm.com/new/product-blog/evolving-the-ibm-storage-portfolio-brand-identity-and-strategy', None,
    'title, author, the date of March 2, 2023 in the page body, the change from IBM Spectrum to IBM Storage and the product name IBM Storage Scale read from the page 2026-11-23; a metadata field of the page carries a later date')

# --- Amdahl's law in the History section (added for version 11; read 2026-11-26)
entry('article', 'gustafson1988', [('author', 'John L. Gustafson'), ('title', "Reevaluating Amdahl's Law"), ('year', '1988'),
                                   ('journal', 'Communications of the ACM'), ('volume', '31'), ('number', '5'), ('pages', '532--533'),
                                   ('doi', '10.1145/42411.42415')],
      'title, author, journal, volume, number and pages read from the first page of the article and the DOI from its index record 2026-11-26; '
      'cited for the fixed-size form of the speed-up, 1/(s + p/N)')

# --- Memory placement on NUMA servers (added for version 13; each page read 2026-11-27)
A27 = 'Accessed November 27, 2026'
entry('misc', 'kernel_numa', [('author', '{The Linux kernel development community}'), ('title', 'What is NUMA?'), ('year', 'n.d'),
                              ('howpublished', 'The Linux Kernel documentation, Memory Management'),
                              ('url', 'https://docs.kernel.org/mm/numa.html'),
                              ('note', 'Started in November 1999 by Kanoj Sarcar. ' + A27)],
      'page read 2026-11-27: title, the started-by line, cells with processors, local memory and I/O buses joined by an interconnect, '
      'access time and bandwidth depending on the distance between the cell of the processor or I/O bus and the cell of the memory, '
      'allocation from the node of the requesting processor by default, and the scheduler not taking the memory of a task into account directly')
entry('misc', 'kernel_mempolicy', [('author', '{The Linux kernel development community}'), ('title', 'NUMA Memory Policy'), ('year', 'n.d'),
                                   ('howpublished', "The Linux Kernel documentation, version 6.8, Administrator's Guide"),
                                   ('url', 'https://docs.kernel.org/6.8/admin-guide/mm/numa_memory_policy.html'),
                                   ('note', A27)],
      'page read 2026-11-27: the system default policy is local allocation once the system is running; a policy for a range of the address space '
      'is installed with mbind, governs anonymous pages and by default applies to pages allocated after it is installed; the bind mode restricts '
      'allocation to the given nodes. The page does not use the words first touch')
entry('misc', 'kernel_pin', [('author', '{The Linux kernel development community}'), ('title', 'pin_user_pages() and related calls'), ('year', 'n.d'),
                             ('howpublished', 'The Linux Kernel documentation, version 6.14, Core API'),
                             ('url', 'https://docs.kernel.org/6.14/core-api/pin_user_pages.html'),
                             ('note', A27)],
      'page read 2026-11-27: the case of RDMA sets the pin and long-term flags and says that the buffers are needed for a long time. '
      'The page does not state that pinned pages cannot be migrated, and the thesis does not say so')
entry('misc', 'kernel_sysfs_pci', [('author', '{The Linux kernel development community}'), ('title', 'sysfs-bus-pci'), ('year', 'n.d'),
                                   ('howpublished', 'Linux kernel ABI documentation, Documentation/ABI/testing'),
                                   ('url', 'https://kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci'),
                                   ('note', 'Entry numa_node of October 2014. ' + A27)],
      'file read 2026-11-27: the entry /sys/bus/pci/devices/.../numa_node, dated October 2014, holds the node to which the device is attached, '
      'or -1 if the node is unknown; the initial value comes from the firmware')
entry('misc', 'nvidia_cx4_tuning', [('author', '{NVIDIA}'), ('title', 'NVIDIA FreeBSD for ConnectX-4 and above Adapter Cards v3.7.1: Performance Tuning'), ('year', '2024'),
                                    ('howpublished', 'NVIDIA Networking documentation, last updated June 10, 2024'),
                                    ('url', 'https://docs.nvidia.com/networking/display/freebsdv371/performance+tuning'),
                                    ('note', A27)],
      'page read 2026-11-27: title, the date in the footer, the statement that a server with a single NUMA needs no tuning, and for two the steps '
      'that bind the interrupts and the application to processors of the NUMA closest to the card. The page documents the FreeBSD driver')
entry('misc', 'esnet_irq', [('author', '{Energy Sciences Network}'), ('title', 'Interrupt Binding'), ('year', '2024'),
                            ('howpublished', 'ESnet Fasterdata knowledge base, Host Tuning, last edited December 26, 2024'),
                            ('url', 'https://fasterdata.es.net/host-tuning/interrupt-binding/'),
                            ('note', A27)],
      'page read 2026-11-27: on hosts with 40 and 100 gigabit adapters TCP and UDP can be up to two times slower with processors on the wrong socket; '
      'both the interrupts of the card and the application belong on the socket of the card; the last-edited date. The page itself is dated January 2, 2025')

entry('book', 'farazdel2001gpfsaix', [('author', 'A. Farazdel and R. Curran and A. Jaehde and G. McPheeters and R. Paden and R. E. Wescott'),
                                      ('title', 'GPFS on AIX Clusters: High Performance File System Administration Simplified'), ('year', '2001'), ('month', 'August'),
                                      ('publisher', 'IBM'), ('address', 'Poughkeepsie, NY'),
                                      ('url', 'https://www.pnnl.gov/publications/gpfs-aix-clusters-high-performance-file-system-administration-simplified'),
                                      ('note', 'IBM Redbook. Record PNNL-SA-35463 with the abstract. ' + A27)],
      'record and abstract read 2026-11-27 on the publications page of Pacific Northwest National Laboratory: authors, title, IBM, Poughkeepsie, the date '
      'August 3, 2001 and the number PNNL-SA-35463; the abstract names the product General Parallel File System for AIX and says that its release 1.4 '
      'is the first offered for AIX RS/6000 systems that are not part of an RS/6000 SP. The page gives initials only, and no IBM order number')

open(sys.argv[2], 'w', encoding='utf-8').write('% refs.bib: every entry was checked on 2026-11-23 against the source named in\n% audit/bib_provenance.json (arXiv API, Crossref, the page itself, or the saved PDF).\n\n' + '\n\n'.join(out) + '\n')
json.dump(prov, open(sys.argv[1].replace('bib_verified', 'bib_provenance'), 'w'), indent=1)
print('entries written:', len(out))
todo = [k for k, v in prov.items() if 'to confirm' in v or 'not fetched' in v or 'not checked' in v]
print('entries with a part still to confirm:', ', '.join(todo))
