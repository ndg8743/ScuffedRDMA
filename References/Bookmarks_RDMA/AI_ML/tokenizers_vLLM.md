# tokenizers - vLLM

- **Source:** https://docs.vllm.ai/en/latest/api/vllm/tokenizers/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# `vllm.tokenizers`
[¶](#vllm.tokenizers)

Modules:

- – Tokenizer for Alpamayo 2 Super.
- –
- –
- –
- – Text encoding adapted from the DeepSeek V4.1 reference encoder.
- – DeepSeek-V4 Encoding
- –
- – `fastokens` backend patch.
- –
- – Tokenizer for Kimi-Audio using TikToken.
- –
- –

Functions:

- – Gets a tokenizer for the given model name via HuggingFace or ModelScope.
- – If `tokenizer` is a `TokenizersBackend`, modify the tokenizer

## `get_tokenizer(tokenizer_name, *args, tokenizer_cls=TokenizerLike, trust_remote_code=False, revision=None, download_dir=None, **kwargs)`
[¶](#vllm.tokenizers.get_tokenizer)

Gets a tokenizer for the given model name via HuggingFace or ModelScope.

## Source code in `vllm/tokenizers/registry.py`

| [208](#__codelineno-0-208) [209](#__codelineno-0-209) [210](#__codelineno-0-210) [211](#__codelineno-0-211) [212](#__codelineno-0-212) [213](#__codelineno-0-213) [214](#__codelineno-0-214) [215](#__codelineno-0-215) [216](#__codelineno-0-216) [217](#__codelineno-0-217) [218](#__codelineno-0-218) [219](#__codelineno-0-219) [220](#__codelineno-0-220) [221](#__codelineno-0-221) [222](#__codelineno-0-222) [223](#__codelineno-0-223) [224](#__codelineno-0-224) [225](#__codelineno-0-225) [226](#__codelineno-0-226) [227](#__codelineno-0-227) [228](#__codelineno-0-228) [229](#__codelineno-0-229) [230](#__codelineno-0-230) [231](#__codelineno-0-231) [232](#__codelineno-0-232) [233](#__codelineno-0-233) [234](#__codelineno-0-234) [235](#__codelineno-0-235) [236](#__codelineno-0-236) [237](#__codelineno-0-237) [238](#__codelineno-0-238) [239](#__codelineno-0-239) [240](#__codelineno-0-240) [241](#__codelineno-0-241) [242](#__codelineno-0-242) [243](#__codelineno-0-243) [244](#__codelineno-0-244) [245](#__codelineno-0-245) [246](#__codelineno-0-246) [247](#__codelineno-0-247) [248](#__codelineno-0-248) [249](#__codelineno-0-249) [250](#__codelineno-0-250) [251](#__codelineno-0-251) [252](#__codelineno-0-252) [253](#__codelineno-0-253) [254](#__codelineno-0-254) [255](#__codelineno-0-255) [256](#__codelineno-0-256) [257](#__codelineno-0-257) [258](#__codelineno-0-258) [259](#__codelineno-0-259) [260](#__codelineno-0-260) [261](#__codelineno-0-261) [262](#__codelineno-0-262) [263](#__codelineno-0-263) [264](#__codelineno-0-264) [265](#__codelineno-0-265) [266](#__codelineno-0-266) [267](#__codelineno-0-267) [268](#__codelineno-0-268) [269](#__codelineno-0-269) [270](#__codelineno-0-270) [271](#__codelineno-0-271) [272](#__codelineno-0-272) [273](#__codelineno-0-273) [274](#__codelineno-0-274) [275](#__codelineno-0-275) [276](#__codelineno-0-276) [277](#__codelineno-0-277) [278](#__codelineno-0-278) [279](#__codelineno-0-279) [280](#__codelineno-0-280) [281](#__codelineno-0-281) [282](#__codelineno-0-282) [283](#__codelineno-0-283) [284](#__codelineno-0-284) [285](#__codelineno-0-285) [286](#__codelineno-0-286) [287](#__codelineno-0-287) [288](#__codelineno-0-288) [289](#__codelineno-0-289) [290](#__codelineno-0-290) [291](#__codelineno-0-291) [292](#__codelineno-0-292) | def get_tokenizer( tokenizer_name: str \| Path, *args, tokenizer_cls: type[_T] = TokenizerLike,  # type: ignore[assignment] trust_remote_code: bool = False, revision: str \| None = None, download_dir: str \| None = None, **kwargs, ) -> _T: """Gets a tokenizer for the given model name via HuggingFace or ModelScope.""" if envs.VLLM_USE_FASTOKENS: # Process-global, idempotent patch that swaps the Rust BPE backend # of any HF fast tokenizer loaded afterwards. No-op for non-HF modes. from .fastokens import apply_fastokens_patch apply_fastokens_patch() requested_name = str(tokenizer_name) tokenizer_mode, tokenizer_name, args, kwargs = cached_resolve_tokenizer_args( tokenizer_name, *args, trust_remote_code=trust_remote_code, revision=revision, download_dir=download_dir, **kwargs, ) if tokenizer_cls == TokenizerLike: tokenizer_cls_ = TokenizerRegistry.load_tokenizer_cls(tokenizer_mode) else: tokenizer_cls_ = tokenizer_cls # Ensure that, if the config were to come from vllm.transformers_utils.config, it is # registered with AutoConfig before the tokenizer is loaded. This is necessary since # tokenizer_cls_.from_pretrained will call AutoConfig.from_pretrained internally. # This may fail for paths that don't have a model config (e.g. LoRA adapters), # which is fine — those don't need custom config registration. # HF-backed tokenizers must receive the HF config. In a dual-format Mistral # repository, auto detection intentionally prefers params.json, but passing # that generic config to AutoTokenizer can select the wrong tokenizer class. config_format = "hf" if tokenizer_cls_ is CachedHfTokenizer else "auto" config = None with contextlib.suppress(ValueError, OSError): config = get_config( tokenizer_name, trust_remote_code=trust_remote_code, revision=revision, code_revision=kwargs.get("code_revision"), config_format=config_format, token=kwargs.get("token"), ) # Some models have an incorrect tokenizer_class on the hub. # For these model types, bypass AutoTokenizer and use TokenizersBackend directly. model_type = getattr(config, "model_type", None) if config else None if model_type in _MODEL_TYPES_WITH_INCORRECT_TOKENIZER_CLASS: from transformers.tokenization_utils_tokenizers import TokenizersBackend logger.debug( "Overriding tokenizer_class to TokenizersBackend for model_type=%r", model_type, ) tokenizer_cls_ = TokenizersBackend if config is not None and tokenizer_cls_ is CachedHfTokenizer: # AutoTokenizer otherwise reloads config.json internally. Reuse the # config that get_config just loaded successfully so a concurrent Hub # cache refresh cannot invalidate the file between the two reads. kwargs.setdefault("config", config) tokenizer = tokenizer_cls_.from_pretrained(tokenizer_name, *args, **kwargs) # Report the Hub ID rather than the local snapshot it was loaded from if tokenizer_mode == "hf" and not envs.VLLM_USE_MODELSCOPE: cast(HfTokenizer, tokenizer).name_or_path = requested_name if model_type in _MODEL_TYPES_WITH_INCORRECT_TOKENIZER_CLASS: from vllm.tokenizers.hf import get_cached_tokenizer tokenizer = get_cached_tokenizer(tokenizer) if not tokenizer.is_fast: logger.warning( "Using a slow tokenizer. This might cause a significant " "slowdown. Consider using a fast tokenizer instead." ) return tokenizer  # type: ignore | 

## `maybe_make_thread_pool(tokenizer, copies=1)`
[¶](#vllm.tokenizers.maybe_make_thread_pool)

If `tokenizer` is a `TokenizersBackend`, modify the tokenizer
in-place to make the public interface thread-safe by routing calls
through a deep-copied tokenizer pool.

Note that:
- Only `TokenizerLike`'s public interface is thread-safe.
  This doesn't include `_tokenizer` property nor any mutation
  methods like `add_special_tokens` or `add_tokens`.
- Adjacent method calls could happen on different deep copies.

## Source code in `vllm/tokenizers/hf.py`

|  | def maybe_make_thread_pool(tokenizer: _T, copies: int = 1): """If `tokenizer` is a `TokenizersBackend`, modify the tokenizer in-place to make the public interface thread-safe by routing calls through a deep-copied tokenizer pool. Note that: - Only ``TokenizerLike``'s public interface is thread-safe. This doesn't include ``_tokenizer`` property nor any mutation methods like ``add_special_tokens`` or ``add_tokens``. - Adjacent method calls could happen on different deep copies. """ if not isinstance(tokenizer, TokenizersBackend) or isinstance( tokenizer, ThreadSafeHFTokenizerMixin ): return tokenizer og_tokenizer = copy.copy(tokenizer) tokenizer_pool: queue.Queue[TokenizersBackend] = queue.Queue() for _ in range(copies): tokenizer_pool.put(copy.deepcopy(og_tokenizer)) @contextlib.contextmanager def _borrow_from_pool(): try: tok = tokenizer_pool.get_nowait() yield tok except queue.Empty: tok = copy.deepcopy(og_tokenizer) yield tok finally: tokenizer_pool.put(tok) class TokenizerPool(tokenizer.__class__, ThreadSafeHFTokenizerMixin):  # type: ignore def apply_chat_template(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.apply_chat_template(*args, **kwargs) def batch_decode(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.batch_decode(*args, **kwargs) def batch_encode(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.batch_encode(*args, **kwargs) def convert_tokens_to_ids(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.convert_tokens_to_ids(*args, **kwargs) def convert_ids_to_tokens(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.convert_ids_to_tokens(*args, **kwargs) def convert_tokens_to_string(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.convert_tokens_to_string(*args, **kwargs) def decode(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.decode(*args, **kwargs) def encode(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok.encode(*args, **kwargs) def __call__(self, *args, **kwargs): with _borrow_from_pool() as tok: return tok(*args, **kwargs) def __reduce__(self): return maybe_make_thread_pool, (og_tokenizer, copies) TokenizerPool.__name__ = f"TokenizerPool{og_tokenizer.__class__.__name__}" tokenizer.__class__ = TokenizerPool # Return the tokenizer: TokenizerPool.__reduce__ reconstructs through this # function, so falling off the end would unpickle to None (issue #45433). return tokenizer |