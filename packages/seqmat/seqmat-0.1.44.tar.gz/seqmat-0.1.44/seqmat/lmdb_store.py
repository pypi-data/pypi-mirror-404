"""LMDB backend for fast gene data loading.

Provides a single memory-mapped key-value store as an alternative to
per-gene pickle files, reducing filesystem metadata overhead on
networked storage (e.g. EFS).

The ``lmdb`` package is an optional dependency.  All public functions
return ``None`` or raise ``ImportError`` gracefully when it is absent.
"""

import functools
import pickle
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config import get_organism_config, get_default_organism, load_config

# ---------------------------------------------------------------------------
# Optional lmdb import
# ---------------------------------------------------------------------------

try:
    import lmdb as _lmdb
except ImportError:
    _lmdb = None  # type: ignore[assignment]


def _require_lmdb():
    if _lmdb is None:
        raise ImportError(
            "The 'lmdb' package is required for LMDB support. "
            "Install it with:  pip install seqmat[lmdb]"
        )


# ---------------------------------------------------------------------------
# Module-level environment cache (one per path, opened once)
# ---------------------------------------------------------------------------

_ENV_CACHE: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_lmdb_config(organism: Optional[str] = None) -> Tuple[Optional[str], bool]:
    """Return ``(lmdb_path, local_staging)`` from the user config.

    If the organism has a per-organism ``gene_lmdb_path`` key that takes
    precedence over the global setting.  Returns ``(None, False)`` when
    LMDB is not configured.
    """
    config = load_config()
    if organism is None:
        organism = get_default_organism()

    # Per-organism override
    org_conf = config.get(organism, {})
    if isinstance(org_conf, dict):
        lmdb_path = org_conf.get("gene_lmdb_path")
        if lmdb_path is not None:
            staging = org_conf.get("gene_lmdb_local_staging", False)
            return str(lmdb_path), bool(staging)

    # Global fallback
    lmdb_path = config.get("gene_lmdb_path")
    staging = config.get("gene_lmdb_local_staging", False)
    return (str(lmdb_path) if lmdb_path else None), bool(staging)


# ---------------------------------------------------------------------------
# LMDB environment management
# ---------------------------------------------------------------------------

def _open_lmdb(path: str, local_staging: bool = False) -> Any:
    """Open (or return cached) read-only LMDB environment at *path*.

    When *local_staging* is ``True`` the database is first copied to
    ``/tmp/seqmat_lmdb_<basename>`` so that reads hit local disk instead
    of a networked filesystem.
    """
    _require_lmdb()

    if local_staging:
        import tempfile
        staging_dir = Path(tempfile.gettempdir()) / f"seqmat_lmdb_{Path(path).name}"
        if not staging_dir.exists():
            shutil.copytree(path, str(staging_dir))
        path = str(staging_dir)

    if path in _ENV_CACHE:
        return _ENV_CACHE[path]

    env = _lmdb.open(
        path,
        readonly=True,
        readahead=True,
        lock=False,
        max_dbs=0,
        map_size=0,  # 0 = use file size (read-only)
    )
    _ENV_CACHE[path] = env
    return env


# ---------------------------------------------------------------------------
# Gene loading
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=512)
def load_gene_from_lmdb(gene_name: str, organism: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Look up *gene_name* in the LMDB store for *organism*.

    Returns the deserialized gene dictionary (same format as the pickle
    files), or ``None`` if LMDB is not configured / gene not found.
    """
    if _lmdb is None:
        return None

    if organism is None:
        organism = get_default_organism()

    lmdb_path, local_staging = get_lmdb_config(organism)
    if lmdb_path is None:
        return None

    try:
        env = _open_lmdb(lmdb_path, local_staging=local_staging)
    except (FileNotFoundError, PermissionError, OSError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"LMDB open failed: {e}")
        return None
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unexpected error opening LMDB: {e}")
        return None

    with env.begin() as txn:
        raw = txn.get(gene_name.encode("utf-8"))
        if raw is None:
            return None
        return pickle.loads(raw)


# ---------------------------------------------------------------------------
# Build utility
# ---------------------------------------------------------------------------

def build_lmdb(
    annotations_dir: Optional[str] = None,
    output_path: Optional[str] = None,
    organism: Optional[str] = None,
) -> str:
    """Build an LMDB database from per-gene pickle files.

    Parameters
    ----------
    annotations_dir : str, optional
        Directory containing biotype sub-folders with ``*.pkl`` files.
        Resolved from the organism config when ``None``.
    output_path : str, optional
        Where to write the LMDB.  Defaults to ``<annotations_dir>/genes.lmdb``.
    organism : str, optional
        Organism key (e.g. ``"hg38"``).

    Returns
    -------
    str
        The path to the created LMDB database.
    """
    _require_lmdb()

    if organism is None:
        organism = get_default_organism()

    if annotations_dir is None:
        config = get_organism_config(organism)
        annotations_dir = str(config["MRNA_PATH"])

    ann_path = Path(annotations_dir)
    if not ann_path.exists():
        raise FileNotFoundError(f"Annotations directory not found: {ann_path}")

    if output_path is None:
        output_path = str(ann_path / "genes.lmdb")

    out = Path(output_path)
    # Remove existing DB if present
    if out.exists():
        shutil.rmtree(str(out))

    pkl_files = sorted(ann_path.glob("**/*.pkl"))
    if not pkl_files:
        raise FileNotFoundError(f"No .pkl files found under {ann_path}")

    # Estimate map size: sum of file sizes * 1.5 for overhead
    total_bytes = sum(f.stat().st_size for f in pkl_files)
    map_size = int(total_bytes * 1.5) + 10 * 1024 * 1024  # +10 MB headroom

    env = _lmdb.open(str(out), map_size=map_size, max_dbs=0)

    genes_written = 0
    skipped = 0
    total_size = 0

    with env.begin(write=True) as txn:
        for pkl_file in pkl_files:
            try:
                raw_bytes = pkl_file.read_bytes()
                # Derive gene name from filename
                # Handle both patterns: "ENSG00000133703_KRAS.pkl" and "mrnas_ENSG00000133703_KRAS.pkl"
                parts = pkl_file.stem.split('_')
                if len(parts) >= 3 and parts[0] == 'mrnas':
                    # Pattern: mrnas_ENSG00000133703_KRAS
                    gene_name = '_'.join(parts[2:])  # Handle gene names with underscores
                elif len(parts) >= 2:
                    # Pattern: ENSG00000133703_KRAS
                    gene_name = '_'.join(parts[1:])  # Handle gene names with underscores
                else:
                    gene_name = pkl_file.stem
                txn.put(gene_name.encode("utf-8"), raw_bytes)
                genes_written += 1
                total_size += len(raw_bytes)
            except Exception as exc:
                print(f"  Skipped {pkl_file.name}: {exc}")
                skipped += 1

    env.close()

    print(f"LMDB built at: {out}")
    print(f"  Genes written: {genes_written:,}")
    print(f"  Total size:    {total_size / (1024 * 1024):.1f} MB")
    if skipped:
        print(f"  Skipped:       {skipped}")

    return str(out)
