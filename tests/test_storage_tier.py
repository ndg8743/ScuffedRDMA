import os

import pytest

from middleware.policy import PolicyEngine
from middleware.rdma_tensor_cache.pmp_controller import StorageDecision
from middleware.rdma_tensor_cache.storage_tier import ALIGN, IntegrityError, StorageTier, benchmark_coalescing
from middleware.telemetry import SignalVector, Telemetry


def blob(i, n=5000):
    return bytes([i % 256]) * n


def test_roundtrip_and_index(tmp_path):
    with StorageTier(str(tmp_path), coalesce=1) as t:
        t.spill("a", blob(1)).result()
        t.spill("b", memoryview(blob(2, 12345))).result()
        assert t.retrieve("a").result() == blob(1)
        assert t.retrieve("b").result() == blob(2, 12345)
        e = t.extent("b")
        assert e.offset % ALIGN == 0 and e.alloc % ALIGN == 0 and e.length == 12345
        with pytest.raises(KeyError):
            t.retrieve("missing").result()


def test_coalescing_waits_for_full_batch(tmp_path):
    t = StorageTier(str(tmp_path), coalesce=3)
    f1, f2 = t.spill("k1", blob(1)), t.spill("k2", blob(2))
    assert t.stats()["pending"] == 2 and not f1.done()
    # pending data is still readable
    assert t.retrieve("k1").result() == blob(1)
    f3 = t.spill("k3", blob(3))
    for f in (f1, f2, f3):
        f.result(timeout=10)
    assert t.stats()["batches_written"] == 1
    t.spill("k4", blob(4))
    t.flush()
    assert t.stats()["batches_written"] == 2
    # one batch is one contiguous extent: k1..k3 back to back
    offs = [t.extent(k).offset for k in ("k1", "k2", "k3")]
    assert offs == sorted(offs) and offs[1] - offs[0] == ALIGN * 2
    got = t.retrieve_batch(["k1", "k2", "k3", "k4"])
    assert got == {"k1": blob(1), "k2": blob(2), "k3": blob(3), "k4": blob(4)}
    t.close(remove=True)
    assert not os.path.exists(t.path)


def test_integrity_check(tmp_path):
    t = StorageTier(str(tmp_path), coalesce=1)
    t.spill("x", blob(7)).result()
    off = t.extent("x").offset
    with open(t.path, "r+b") as f:
        f.seek(off + 10)
        f.write(b"\xff")
    with pytest.raises(IntegrityError):
        t.retrieve("x").result()
    with pytest.raises(IntegrityError):
        t.retrieve_batch(["x"])
    t.close()


def test_free_list_reuse_and_tail_shrink(tmp_path):
    t = StorageTier(str(tmp_path), coalesce=1)
    for k in "abc":
        t.spill(k, blob(1, ALIGN)).result()
    off_b = t.extent("b").offset
    assert t.delete("b") and not t.delete("b")
    assert t.stats()["free_extents"] == 1
    t.spill("d", blob(2, 100)).result()      # fits in b's slot
    assert t.extent("d").offset == off_b
    assert t.stats()["free_extents"] == 0
    end = t.stats()["file_bytes"]
    t.delete("c")
    assert t.stats()["file_bytes"] == end - ALIGN  # tail released, not on the free list
    # overwrite replaces the old extent
    t.spill("a", blob(9, 10)).result()
    assert t.retrieve("a").result() == blob(9, 10)
    t.close()


def test_o_direct_active_or_clean_fallback(tmp_path):
    t = StorageTier(str(tmp_path), coalesce=2, o_direct=True)
    assert t.o_direct in (True, False)
    assert t.o_direct_reason in ("active",) or "buffered" in t.o_direct_reason
    t.spill("a", blob(3, 777))
    t.spill("b", blob(4, 9000)).result()
    assert t.retrieve("a").result() == blob(3, 777)
    assert t.retrieve_batch(["a", "b"])["b"] == blob(4, 9000)
    t.close()


def test_telemetry_and_spill_if(tmp_path):
    tel = Telemetry(node="t")
    t = StorageTier(str(tmp_path), coalesce=1, telemetry=tel)
    assert t.spill_if("cold", "a", blob(1)) is None
    t.spill_if(StorageDecision.SPILL, "b", blob(2)).result()
    d = PolicyEngine.default_policy().decide(
        SignalVector(size_bytes=8 << 20, role="kv", phase="prefill"), {"gpu_mem_util": 0.97, "link_util": 0.0})
    assert d.route == "spill"
    t.spill_if(d, "c", blob(3)).result()
    t.retrieve("c").result()
    s = tel.snapshot()["classes"]["storage"]
    assert s["ops"] == 3 and s["bytes"] == 3 * 5000
    assert "a" not in t and "b" in t
    t.close()


def test_closed_tier_rejects(tmp_path):
    t = StorageTier(str(tmp_path))
    t.close()
    with pytest.raises(RuntimeError):
        t.spill("a", b"x")


def test_bad_args(tmp_path):
    with pytest.raises(ValueError):
        StorageTier(str(tmp_path), coalesce=0)


def test_benchmark_shape_matches_previous_results(tmp_path):
    r = benchmark_coalescing(str(tmp_path), block_bytes=16 * 1024, coalesce_list=(1, 2, 5), batches=3,
                             block_sizes=[16 * 1024, 32 * 1024], meta={"bits": 3, "dim": 128})
    for k in ("hostname", "single_block_kb", "coalesce_results", "sweeps", "bits"):
        assert k in r
    row = r["coalesce_results"][0]
    for k in ("coalesce", "payload_kb", "write_us", "write_mbps", "read_us", "read_mbps"):
        assert k in row
    assert [x["coalesce"] for x in r["coalesce_results"]] == [1, 2, 5]
    assert len(r["sweeps"]) == 2 and r["sweeps"][1]["single_block_kb"] == 32
    assert os.listdir(tmp_path) == []
