"""Tests for the LMDB backend (seqmat.lmdb_store)."""

import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Skip entire module if lmdb is not installed
lmdb = pytest.importorskip("lmdb")

from seqmat.lmdb_store import build_lmdb, load_gene_from_lmdb, _ENV_CACHE, get_lmdb_config


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_gene_dict(gene_name, gene_id="ENSG_FAKE", chrm="chr1", rev=False):
    return {
        "gene_name": gene_name,
        "gene_id": gene_id,
        "chrm": chrm,
        "rev": rev,
        "transcripts": {
            "ENST_001": {
                "transcript_id": "ENST_001",
                "transcript_biotype": "protein_coding",
            }
        },
    }


@pytest.fixture()
def annotations_dir(tmp_path):
    """Create a fake annotations directory with a few pickle files."""
    ann = tmp_path / "annotations"
    biotype_dir = ann / "protein_coding"
    biotype_dir.mkdir(parents=True)

    for name in ("KRAS", "TP53", "BRCA1"):
        gene = _make_gene_dict(name)
        pkl_path = biotype_dir / f"ENSG_FAKE_{name}.pkl"
        pkl_path.write_bytes(pickle.dumps(gene))

    return ann


# ---------------------------------------------------------------------------
# build_lmdb
# ---------------------------------------------------------------------------

class TestBuildLmdb:
    def test_build_creates_db(self, annotations_dir, tmp_path):
        out = tmp_path / "genes.lmdb"
        result = build_lmdb(
            annotations_dir=str(annotations_dir),
            output_path=str(out),
        )
        assert Path(result).exists()
        # Verify contents
        env = lmdb.open(result, readonly=True, lock=False)
        with env.begin() as txn:
            assert txn.get(b"KRAS") is not None
            assert txn.get(b"TP53") is not None
            assert txn.get(b"BRCA1") is not None
            data = pickle.loads(txn.get(b"KRAS"))
            assert data["gene_name"] == "KRAS"
        env.close()

    def test_build_stats_printed(self, annotations_dir, tmp_path, capsys):
        build_lmdb(
            annotations_dir=str(annotations_dir),
            output_path=str(tmp_path / "genes.lmdb"),
        )
        captured = capsys.readouterr()
        assert "Genes written: 3" in captured.out

    def test_build_no_pkl_raises(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(FileNotFoundError, match="No .pkl files"):
            build_lmdb(annotations_dir=str(empty), output_path=str(tmp_path / "out.lmdb"))

    def test_build_missing_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            build_lmdb(annotations_dir=str(tmp_path / "nope"), output_path=str(tmp_path / "out.lmdb"))


# ---------------------------------------------------------------------------
# load_gene_from_lmdb
# ---------------------------------------------------------------------------

class TestLoadGene:
    def test_load_returns_gene(self, annotations_dir, tmp_path):
        db_path = str(tmp_path / "genes.lmdb")
        build_lmdb(annotations_dir=str(annotations_dir), output_path=db_path)

        # Clear caches
        load_gene_from_lmdb.cache_clear()
        _ENV_CACHE.clear()

        with patch("seqmat.lmdb_store.get_lmdb_config", return_value=(db_path, False)):
            result = load_gene_from_lmdb("KRAS", organism="hg38")
            assert result is not None
            assert result["gene_name"] == "KRAS"

    def test_load_missing_gene_returns_none(self, annotations_dir, tmp_path):
        db_path = str(tmp_path / "genes.lmdb")
        build_lmdb(annotations_dir=str(annotations_dir), output_path=db_path)

        load_gene_from_lmdb.cache_clear()
        _ENV_CACHE.clear()

        with patch("seqmat.lmdb_store.get_lmdb_config", return_value=(db_path, False)):
            result = load_gene_from_lmdb("NONEXISTENT", organism="hg38")
            assert result is None

    def test_load_no_config_returns_none(self):
        load_gene_from_lmdb.cache_clear()
        _ENV_CACHE.clear()

        with patch("seqmat.lmdb_store.get_lmdb_config", return_value=(None, False)):
            result = load_gene_from_lmdb("KRAS", organism="hg38")
            assert result is None

    def test_lru_cache_hit(self, annotations_dir, tmp_path):
        db_path = str(tmp_path / "genes.lmdb")
        build_lmdb(annotations_dir=str(annotations_dir), output_path=db_path)

        load_gene_from_lmdb.cache_clear()
        _ENV_CACHE.clear()

        with patch("seqmat.lmdb_store.get_lmdb_config", return_value=(db_path, False)):
            r1 = load_gene_from_lmdb("TP53", organism="hg38")
            r2 = load_gene_from_lmdb("TP53", organism="hg38")
            assert r1 == r2
            info = load_gene_from_lmdb.cache_info()
            assert info.hits >= 1


# ---------------------------------------------------------------------------
# get_lmdb_config
# ---------------------------------------------------------------------------

class TestGetLmdbConfig:
    def test_returns_none_by_default(self):
        with patch("seqmat.lmdb_store.load_config", return_value={"default_organism": "hg38"}):
            path, staging = get_lmdb_config("hg38")
            assert path is None
            assert staging is False

    def test_per_organism_config(self):
        config = {
            "default_organism": "hg38",
            "hg38": {
                "gene_lmdb_path": "/data/genes.lmdb",
                "gene_lmdb_local_staging": True,
            },
        }
        with patch("seqmat.lmdb_store.load_config", return_value=config):
            path, staging = get_lmdb_config("hg38")
            assert path == "/data/genes.lmdb"
            assert staging is True

    def test_global_config_fallback(self):
        config = {
            "default_organism": "hg38",
            "gene_lmdb_path": "/global/genes.lmdb",
        }
        with patch("seqmat.lmdb_store.load_config", return_value=config):
            path, staging = get_lmdb_config("hg38")
            assert path == "/global/genes.lmdb"


# ---------------------------------------------------------------------------
# Gene.from_file integration
# ---------------------------------------------------------------------------

class TestGeneFromFileFallback:
    def test_falls_back_to_pickle_when_no_lmdb(self):
        """Gene.from_file should still work when LMDB returns None."""
        from seqmat.gene import Gene

        with patch("seqmat.lmdb_store.load_gene_from_lmdb", return_value=None), \
             patch("seqmat.gene.get_organism_config", return_value={"MRNA_PATH": "/nonexistent"}), \
             patch("seqmat.gene.get_default_organism", return_value="hg38"):
            load_gene_from_lmdb.cache_clear()
            result = Gene.from_file("FAKEGENE", organism="hg38")
            # Should return None because /nonexistent doesn't exist either
            assert result is None
