import hashlib
import io
import re

import pandas as pd

from apps.analytics.services.iqvia_i18n import dim_label, tr, tr_format
from apps.analytics.models.iqvia_models import (
    IQV_ATC1,
    IQV_ATC2,
    IQV_ATC3,
    IQV_ATC4,
    IQV_BrandDet,
    IQV_Company,
    IQV_ComType,
    IQV_Corp,
    IQV_EthStat,
    IQV_EthStatGrp,
    IQV_GenFlag,
    IQV_ITMATrans,
    IQV_MoleFam,
    IQV_MoleSubFam,
    IQV_Molecule,
    IQV_NFC1,
    IQV_NFC2,
    IQV_NFC3,
    IQV_OTC1,
    IQV_OTC2,
    IQV_OTC3,
    IQV_OTC4,
    IQV_Pack,
    IQV_PackForm,
    IQV_Product,
    IQV_RegStat,
)

# Rows carrying any of these are pivot leftovers, never real data
# UNKNOWN is deliberately absent, "UNKNOWN MANUF." is a real data if an unknown company
NOISE_TOKENS = [
    "PIVOTTABLE",
    "INDONESIA_NSA_DW",
    "SUBTOTAL",
    "GRAND TOTAL",
    "(BLANK)",
]

# Cell values that mean empty
BLANK_VALUES = ["", "NAN", "NONE", "NULL", "<NA>", "(BLANK)", "-"]

# How a code and a name sit inside one cell
PARSE_PLAIN = "plain"            # cell is the name, nothing to split
PARSE_DASH_SPACE = "dash_space"  # "A01 - STOMATOLOGICALS"
PARSE_DASH = "dash"              # "10-CIRCULATORY PRODUCTS"
PARSE_ETHSTAT = "ethstat"        # name plus group suffix
PARSE_PRODUCT = "product"        # "3TC - GSK", suffix is the company code
PARSE_PACK = "pack"              # many files merged on the Pack column
PARSE_ITMA = "itma"              # pack key plus quarter

# Header row is searched inside this many first rows
HEADER_SCAN_ROWS = 15

# Company code hides in the Product column suffix
COMPANY_CODE_LEN = 3


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: IMPORT_DIMENSIONS                                   ║
# ║  Type: Constant registry                                   ║
# ║  Purpose: Master map of every importable IQVIA dimension   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: Aug/27-2026 by Akram, code_col + parent parse    ║
# ╚════════════════════════════════════════════════════════════╝
# key       : id used in query string, same keys as DIMENSIONS
# label     : text shown to user
# model     : target model
# table     : postgres table name
# level     : dependency depth, 0 has no parent
# family    : cascade group in the import dropdown
# match     : field used to decide insert or update
# parse     : how the main cell splits into code and name
# main_col  : header text of the column holding the item itself
# code_col  : header text holding the code, None means split it from main_col
# extra_cols: columns needed on top of main and parents
# parents   : list of parent rules
#   dim      : parent dimension key
#   field    : model field on this side
#   column   : header text holding the parent value
#   parse    : how to read the parent cell, PARSE_PLAIN uses it as is
#   on       : parent field the value is matched against
#   required : True blocks the whole file when it cannot resolve
# archive   : True copies the old row as deleted before overwriting
IMPORT_DIMENSIONS = {
    # ── Level 0, no parent ────────────────────────────────────
    "corp": {
        "label": "Corporation", "model": IQV_Corp, "table": "analytics_iqv_corp",
        "level": 0, "family": "corporation", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Corporation", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "comtype": {
        "label": "Company Type", "model": IQV_ComType, "table": "analytics_iqv_comtype",
        "level": 0, "family": "corporation", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Company Type", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "ethgrp": {
        "label": "Ethical Status Group", "model": IQV_EthStatGrp,
        "table": "analytics_iqv_ethstatgrp", "level": 0, "family": "ethical",
        "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Ethical Status Group", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "genflag": {
        "label": "Generic Flag", "model": IQV_GenFlag, "table": "analytics_iqv_genflag",
        "level": 0, "family": "brand", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Generic Flag", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "regstat": {
        "label": "Registration Status", "model": IQV_RegStat,
        "table": "analytics_iqv_regstat", "level": 0, "family": "product",
        "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Product Registration Status", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "packform": {
        "label": "Pack Form", "model": IQV_PackForm, "table": "analytics_iqv_packform",
        "level": 0, "family": "product", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Pack Form", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "molefam": {
        "label": "Molecule Family", "model": IQV_MoleFam, "table": "analytics_iqv_molefam",
        "level": 0, "family": "molecule", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Family", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "atc1": {
        "label": "ATC 1", "model": IQV_ATC1, "table": "analytics_iqv_atc1",
        "level": 0, "family": "atc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "ATC1", "code_col": "ATC1 Code", "extra_cols": [],
        "parents": [], "archive": True,
    },
    "otc1": {
        "label": "OTC 1", "model": IQV_OTC1, "table": "analytics_iqv_otc1",
        "level": 0, "family": "otc", "match": "code", "parse": PARSE_DASH,
        "main_col": "OTC1", "code_col": None, "extra_cols": [],
        "parents": [], "archive": True,
    },
    "nfc1": {
        "label": "NFC 1", "model": IQV_NFC1, "table": "analytics_iqv_nfc1",
        "level": 0, "family": "nfc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "NFC1", "code_col": "NFC1 Code", "extra_cols": [],
        "parents": [], "archive": True,
    },
    # ── Level 1 ───────────────────────────────────────────────
    "company": {
        "label": "Company", "model": IQV_Company, "table": "analytics_iqv_company",
        "level": 1, "family": "corporation", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Company", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "comtype", "field": "comtype_id", "column": "Company Type",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
            {"dim": "corp", "field": "corporation_id", "column": "Corporation",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
    },
    "ethstat": {
        "label": "Ethical Status", "model": IQV_EthStat, "table": "analytics_iqv_ethstat",
        "level": 1, "family": "ethical", "match": "name", "parse": PARSE_ETHSTAT,
        "main_col": "Ethical Status", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "ethgrp", "field": "group_id", "column": "Ethical Status Group",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
    },
    "branddet": {
        "label": "Brand Detail", "model": IQV_BrandDet, "table": "analytics_iqv_branddet",
        "level": 1, "family": "brand", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Branded Details", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "genflag", "field": "gen_flag_id", "column": "Generic Flag",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
    },
    "molesubfam": {
        "label": "Molecule Sub Family", "model": IQV_MoleSubFam,
        "table": "analytics_iqv_molesubfam", "level": 1, "family": "molecule",
        "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Sub Family", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "molefam", "field": "family_id", "column": "Family",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
    },
    "atc2": {
        "label": "ATC 2", "model": IQV_ATC2, "table": "analytics_iqv_atc2",
        "level": 1, "family": "atc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "ATC2", "code_col": "ATC2 Code", "extra_cols": [],
        "parents": [
            {"dim": "atc1", "field": "atc1_id", "column": "ATC1 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": True},
        ],
        "archive": True,
    },
    "otc2": {
        "label": "OTC 2", "model": IQV_OTC2, "table": "analytics_iqv_otc2",
        "level": 1, "family": "otc", "match": "code", "parse": PARSE_DASH,
        "main_col": "OTC2", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "otc1", "field": "otc1_id", "column": "OTC1",
             "parse": PARSE_DASH, "on": "code", "required": True},
        ],
        "archive": True,
    },
    "nfc2": {
        "label": "NFC 2", "model": IQV_NFC2, "table": "analytics_iqv_nfc2",
        "level": 1, "family": "nfc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "NFC2", "code_col": "NFC2 Code", "extra_cols": [],
        "parents": [
            {"dim": "nfc1", "field": "nfc1_id", "column": "NFC1 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": True},
        ],
        "archive": True,
    },
    # ── Level 2 ───────────────────────────────────────────────
    "product": {
        "label": "Product", "model": IQV_Product, "table": "analytics_iqv_product",
        "level": 2, "family": "product", "match": "name", "parse": PARSE_PRODUCT,
        "main_col": "Product", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "company", "field": "company_id", "column": "Company",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
        # The parsed code is the company suffix, it belongs to IQV_Company only
        "store_code": False,
    },
    "molecule": {
        "label": "Molecule", "model": IQV_Molecule, "table": "analytics_iqv_molecule",
        "level": 2, "family": "molecule", "match": "name", "parse": PARSE_PLAIN,
        "main_col": "Molecule", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "molesubfam", "field": "subfamily_id", "column": "Sub Family",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
        ],
        "archive": True,
    },
    "atc3": {
        "label": "ATC 3", "model": IQV_ATC3, "table": "analytics_iqv_atc3",
        "level": 2, "family": "atc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "ATC3", "code_col": "ATC3 Code", "extra_cols": [],
        "parents": [
            {"dim": "atc2", "field": "atc2_id", "column": "ATC2 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": True},
        ],
        "archive": True,
    },
    "otc3": {
        "label": "OTC 3", "model": IQV_OTC3, "table": "analytics_iqv_otc3",
        "level": 2, "family": "otc", "match": "code", "parse": PARSE_DASH,
        "main_col": "OTC3", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "otc2", "field": "otc2_id", "column": "OTC2",
             "parse": PARSE_DASH, "on": "code", "required": True},
        ],
        "archive": True,
    },
    "nfc3": {
        "label": "NFC 3", "model": IQV_NFC3, "table": "analytics_iqv_nfc3",
        "level": 2, "family": "nfc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "NFC3", "code_col": "NFC3 Code", "extra_cols": [],
        "parents": [
            {"dim": "nfc2", "field": "nfc2_id", "column": "NFC2 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": True},
        ],
        "archive": True,
    },
    # ── Level 3 ───────────────────────────────────────────────
    "atc4": {
        "label": "ATC 4", "model": IQV_ATC4, "table": "analytics_iqv_atc4",
        "level": 3, "family": "atc", "match": "code", "parse": PARSE_DASH_SPACE,
        "main_col": "ATC4", "code_col": "ATC4 Code", "extra_cols": [],
        "parents": [
            {"dim": "atc3", "field": "atc3_id", "column": "ATC3 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": True},
        ],
        "archive": True,
    },
    "otc4": {
        "label": "OTC 4", "model": IQV_OTC4, "table": "analytics_iqv_otc4",
        "level": 3, "family": "otc", "match": "code", "parse": PARSE_DASH,
        "main_col": "OTC4", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "otc3", "field": "otc3_id", "column": "OTC3",
             "parse": PARSE_DASH, "on": "code", "required": True},
        ],
        "archive": True,
    },
    # ── Level 4, multi file ───────────────────────────────────
    "pack": {
        "label": "Pack", "model": IQV_Pack, "table": "analytics_iqv_pack",
        "level": 4, "family": "product", "match": "name", "parse": PARSE_PACK,
        "main_col": "Pack", "code_col": None, "extra_cols": [],
        "parents": [
            {"dim": "product", "field": "product_id", "column": "Product",
             "parse": PARSE_PLAIN, "on": "name", "required": True},
            {"dim": "packform", "field": "form_id", "column": "Pack Form",
             "parse": PARSE_PLAIN, "on": "name", "required": False},
            {"dim": "regstat", "field": "regstat_id",
             "column": "Product Registration Status",
             "parse": PARSE_PLAIN, "on": "name", "required": False},
            {"dim": "ethgrp", "field": "ethstatgrp_id", "column": "Ethical Status Group",
             "parse": PARSE_PLAIN, "on": "name", "required": False},
            {"dim": "ethstat", "field": "ethstat_id", "column": "Ethical Status",
             "parse": PARSE_PLAIN, "on": "name", "required": False},
            {"dim": "branddet", "field": "branddet_id", "column": "Branded Details",
             "parse": PARSE_PLAIN, "on": "name", "required": False},
            {"dim": "atc4", "field": "atc4_id", "column": "ATC4 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": False},
            {"dim": "otc4", "field": "otc4_id", "column": "OTC4",
             "parse": PARSE_DASH_SPACE, "on": "code", "required": False},
            {"dim": "nfc3", "field": "nfc3_id", "column": "NFC3 Code",
             "parse": PARSE_PLAIN, "on": "code", "required": False},
        ],
        "archive": True,
    },
    # ── Level 5 ───────────────────────────────────────────────
    "itmatrans": {
        "label": "ITMA Transaction", "model": IQV_ITMATrans,
        "table": "analytics_iqv_itmatrans", "level": 5, "family": "transaction",
        "match": "name", "parse": PARSE_ITMA,
        "main_col": "Pack", "code_col": None, "extra_cols": ["Quarter"],
        "parents": [
            {"dim": "pack", "field": "pack_id", "column": "Pack",
             "parse": PARSE_PLAIN, "on": "key", "required": True},
        ],
        "archive": True,
    },
}

# Labels double as the upload order, users read them top to bottom
FAMILY_LABELS = {
    "classification": "1. Klasifikasi IQVIA",
    "dep0": "2. Master Dasar",
    "dep1": "3. Company & Brand",
    "dep2": "4. Product & Molecule",
    "dep3": "5. Pack",
    "dep4": "6. Transaksi ITMA",
}

# Third cascade level, only IQVIA Classification splits this far
IMPORT_SUBGROUP = {
    "atc1": "atc", "atc2": "atc", "atc3": "atc", "atc4": "atc",
    "otc1": "otc", "otc2": "otc", "otc3": "otc", "otc4": "otc",
    "nfc1": "nfc", "nfc2": "nfc", "nfc3": "nfc",
}

SUBGROUP_LABELS = {"atc": "ATC", "otc": "OTC", "nfc": "NFC"}

SUBGROUP_ORDER = ["atc", "otc", "nfc"]

# Cascade group per dimension, classification first then dependency depth
IMPORT_GROUP = {
    "atc1": "classification", "atc2": "classification",
    "atc3": "classification", "atc4": "classification",
    "otc1": "classification", "otc2": "classification",
    "otc3": "classification", "otc4": "classification",
    "nfc1": "classification", "nfc2": "classification", "nfc3": "classification",
    "corp": "dep0", "comtype": "dep0", "ethgrp": "dep0", "genflag": "dep0",
    "regstat": "dep0", "packform": "dep0", "molefam": "dep0",
    "company": "dep1", "ethstat": "dep1", "branddet": "dep1", "molesubfam": "dep1",
    "product": "dep2", "molecule": "dep2",
    "pack": "dep3",
    "itmatrans": "dep4",
}

# Pack export is sliced by attribute, the extra column names the slice
# IQVIA labels the classification slices with a Code suffix
PACK_PARTS = {
    "Product": "pack_product",
    "Pack Form": "pack_packform",
    "Product Registration Status": "pack_regstat",
    "Ethical Status": "pack_ethstat",
    "Ethical Status Group": "pack_ethstatgrp",
    "Branded Details": "pack_branddet",
    "ATC4 Code": "pack_atc4",
    "OTC4": "pack_otc4",
    "NFC3 Code": "pack_nfc3",
    "Pack Size": "pack_size",
    "Pack Strength": "pack_strength",
    "Pack Volume": "pack_volume",
    "Pack Molecule String": "pack_molstring",
    "Pack Launch Date": "pack_launchdate",
}

# Pack cannot be committed until this slice is present
PACK_REQUIRED_PARTS = ["pack_product"]


# Dimension config, None when key is unknown
def get_import_dimension(key):
    return IMPORT_DIMENSIONS.get(key)


# True when key is a registered import dimension
def is_valid_import_dimension(key):
    return key in IMPORT_DIMENSIONS


# Family order copied from DIMENSIONS, molecule and transaction are extras
FAMILY_ORDER = ["classification", "dep0", "dep1", "dep2", "dep3", "dep4"]

# Item order inside a family, same sequence the Trendline picker shows
DIMENSION_ORDER = [
    "atc1", "atc2", "atc3", "atc4",
    "otc1", "otc2", "otc3", "otc4",
    "nfc1", "nfc2", "nfc3",
    "corp", "comtype", "genflag", "ethgrp", "regstat", "packform", "molefam",
    "company", "branddet", "ethstat", "molesubfam",
    "product", "molecule",
    "pack",
    "itmatrans",
]



# Position in an order list, unlisted keys fall to the end
def order_index(sequence, key):
    return sequence.index(key) if key in sequence else len(sequence)


# Dimensions grouped for the cascade dropdown
# A group with "subgroups" renders a third column, otherwise "items" is final
def get_import_groups():
    buckets = {}
    for key, cfg in IMPORT_DIMENSIONS.items():
        family = IMPORT_GROUP.get(key, "dep0")
        buckets.setdefault(family, []).append(
            {
                "key": key,
                "label": dim_label(key, cfg["label"]),
                "level": cfg["level"],
                "parents": [p["dim"] for p in cfg["parents"]],
                "subgroup": IMPORT_SUBGROUP.get(key),
            }
        )

    result = []
    for family, items in buckets.items():
        items = sorted(items, key=lambda x: order_index(DIMENSION_ORDER, x["key"]))
        entry = {
            "family": family,
            "label": tr("fam_" + family, FAMILY_LABELS.get(family, family)),
            "items": items,
            "subgroups": [],
        }
        if all(item["subgroup"] for item in items):
            nested = {}
            for item in items:
                nested.setdefault(item["subgroup"], []).append(item)
            entry["subgroups"] = sorted(
                (
                    {
                        "key": sub,
                        "label": tr("sub_" + sub, SUBGROUP_LABELS.get(sub, sub)),
                        "items": rows,
                    }
                    for sub, rows in nested.items()
                ),
                key=lambda x: order_index(SUBGROUP_ORDER, x["key"]),
            )
        result.append(entry)

    return sorted(result, key=lambda x: order_index(FAMILY_ORDER, x["family"]))


# Every ancestor of a dimension, nearest first
def get_parent_chain(key):
    chain = []
    seen = set()
    queue = [p["dim"] for p in IMPORT_DIMENSIONS[key]["parents"]]
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        chain.append(current)
        queue += [p["dim"] for p in IMPORT_DIMENSIONS[current]["parents"]]
    return chain


# Sha256 of the raw upload, blocks the same file twice
def build_file_hash(raw_bytes):
    return hashlib.sha256(raw_bytes).hexdigest()


# Lowercase dash slug, same shape the old scripts produced
def build_slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


# Header text without case, spaces or punctuation noise
def normalize_header(text):
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


# True when the cell means empty
def is_blank(value):
    return str(value).strip().upper() in BLANK_VALUES


# True when the cell is a pivot leftover
def is_noise(value):
    upper = str(value).strip().upper()
    for token in NOISE_TOKENS:
        if token in upper:
            return True
    return False


# Whitespace collapsed, quotes left alone because the ORM escapes them
def clean_text(value):
    return re.sub(r"\s+", " ", str(value)).strip()


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: read_dataframe                                      ║
# ║  Type: Helper function                                     ║
# ║  Purpose: Load an upload into a raw headerless dataframe   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
def read_dataframe(raw_bytes, file_type):
    if file_type == "csv":
        for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
            try:
                df = pd.read_csv(
                    io.BytesIO(raw_bytes), header=None, dtype=str, encoding=encoding
                )
                return df, None
            except UnicodeDecodeError:
                continue
        return None, tr("err_csv_encoding")
    try:
        return pd.read_excel(io.BytesIO(raw_bytes), header=None, dtype=str), None
    except Exception as error:
        return None, tr_format("err_excel_read", {"error": error})


# Index of the row holding the real header, None when not found
def find_header_row(df, wanted):
    targets = [normalize_header(w) for w in wanted]
    for index in range(min(HEADER_SCAN_ROWS, len(df))):
        cells = [normalize_header(v) for v in df.iloc[index].tolist()]
        if all(target in cells for target in targets):
            return index
    return None


# Map wanted header text to the real column label
def map_columns(columns, wanted):
    lookup = {normalize_header(c): c for c in columns}
    mapping = {}
    missing = []
    for want in wanted:
        real = lookup.get(normalize_header(want))
        if real is None:
            missing.append(want)
        else:
            mapping[want] = real
    return mapping, missing


# Split one cell into code and name following the given style
def split_code_name(value, style):
    text = clean_text(value)
    if style == PARSE_DASH_SPACE:
        if " - " in text:
            code, name = text.split(" - ", 1)
            return code.strip().upper(), name.strip()
        return "", text
    if style == PARSE_DASH:
        if "-" in text:
            code, name = text.split("-", 1)
            return code.strip().upper(), name.strip()
        return "", text
    if style == PARSE_PRODUCT:
        # "3TC - GSK", the suffix is the company code
        if " - " in text:
            name, code = text.rsplit(" - ", 1)
            code = code.strip().upper()
            if len(code) <= COMPANY_CODE_LEN:
                return code, name.strip()
        return "", text
    return "", text


# Ethical status name carries its group as a suffix, see ethstat.py
def build_ethstat_name(raw_name, raw_group):
    base = clean_text(raw_name).title().replace("Otc", "OTC")
    group = clean_text(raw_group).upper()
    if "ETHICAL" in group:
        return f"{base} (Eth)"
    if "FREE" in group:
        return f"{base} (Free)"
    return f"{base} ({clean_text(raw_group).title()})"


# Which pack slice this file is, None when it is not a pack file
def detect_pack_part(columns):
    normalized = {normalize_header(c) for c in columns}
    if normalize_header("Pack") not in normalized:
        return None
    for column, part in PACK_PARTS.items():
        if normalize_header(column) in normalized:
            return part
    return None


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: parse_file                                          ║
# ║  Type: Service function                                    ║
# ║  Purpose: Turn one raw upload into clean dimension rows    ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/27-2026 by Akram                             ║
# ║  Updates: Aug/27-2026 by Akram, code_col + parent parse    ║
# ╚════════════════════════════════════════════════════════════╝
# Returns a dict, "error" is filled when the file cannot be used
def parse_file(raw_bytes, file_type, dim_key):
    cfg = get_import_dimension(dim_key)
    if cfg is None:
        return {"error": tr("err_unknown_dimension")}

    raw_df, error = read_dataframe(raw_bytes, file_type)
    if error:
        return {"error": error}

    # Pack slices carry different second columns, so only Pack is mandatory
    if cfg["parse"] == PARSE_PACK:
        required_cols = [cfg["main_col"]]
    else:
        required_cols = [cfg["main_col"]] + cfg["extra_cols"]
        required_cols += [p["column"] for p in cfg["parents"]]

    header_row = find_header_row(raw_df, required_cols)
    if header_row is None:
        found = [clean_text(v) for v in raw_df.iloc[:HEADER_SCAN_ROWS].values.ravel()
                 if not is_blank(v)]
        return {
            "error": tr_format(
                "err_header_not_found", {"columns": ", ".join(required_cols)}
            ),
            "found_cells": found[:25],
        }

    df = raw_df.copy()
    df.columns = [clean_text(c) for c in df.iloc[header_row].tolist()]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    mapping, missing = map_columns(df.columns, required_cols)
    if missing:
        return {
            "error": tr_format("err_missing_columns", {"columns": ", ".join(missing)}),
            "found_columns": [str(c) for c in df.columns],
        }

    # Code column is optional, fall back to splitting the main cell
    code_col = None
    if cfg["code_col"]:
        found, _ = map_columns(df.columns, [cfg["code_col"]])
        code_col = found.get(cfg["code_col"])

    # Parent columns are optional on pack slices
    for parent in cfg["parents"]:
        if parent["column"] not in mapping:
            found, _ = map_columns(df.columns, [parent["column"]])
            if parent["column"] in found:
                mapping[parent["column"]] = found[parent["column"]]

    part = detect_pack_part(df.columns) if cfg["parse"] == PARSE_PACK else None
    main_col = mapping[cfg["main_col"]]

    # Merged parent cells arrive empty, carry the value down
    for parent in cfg["parents"]:
        column = mapping.get(parent["column"])
        if column is not None and column != main_col:
            df[column] = df[column].ffill()

    # Column lists beat iterrows by a wide margin on large files
    col_values = {name: df[name].tolist() for name in df.columns}
    main_values = col_values[main_col]
    code_values = col_values[code_col] if code_col else None
    parent_cols = [
        (p, col_values.get(mapping.get(p["column"])) if mapping.get(p["column"]) else None)
        for p in cfg["parents"]
    ]
    raw_items = list(col_values.items())

    rows = []
    seen = set()
    rows_read = len(df)
    rows_noise = 0
    rows_duplicate = 0
    code_mismatch = 0

    for index in range(rows_read):
        main_value = main_values[index]

        if is_blank(main_value) or is_noise(main_value):
            rows_noise += 1
            continue

        code_value = code_values[index] if code_values is not None else None
        if code_value is not None and is_noise(code_value):
            rows_noise += 1
            continue

        # A real code never carries a separator, flattened csv subtotals do
        if code_value is not None and " - " in clean_text(code_value):
            rows_noise += 1
            continue

        main_clean = clean_text(main_value)
        split_code, split_name = split_code_name(main_value, cfg["parse"])

        if cfg["parse"] in (PARSE_PLAIN, PARSE_PACK, PARSE_ITMA, PARSE_ETHSTAT,
                            PARSE_PRODUCT):
            name = main_clean
        else:
            name = split_name

        if code_col and not is_blank(code_value):
            code = clean_text(code_value).upper()
            if split_code and split_code != code:
                code_mismatch += 1
        else:
            code = split_code

        parents = {}
        noise_parent = False
        for parent, values in parent_cols:
            value = values[index] if values is not None else None
            if value is not None and is_noise(value):
                noise_parent = True
                break
            if is_blank(value):
                parents[parent["dim"]] = ""
                continue
            # Csv subtotal rows repeat the main cell into the parent column
            parent_text = clean_text(value)
            if cfg["parse"] == PARSE_PACK and parent_text == main_clean:
                noise_parent = True
                break
            if cfg["match"] == "code" and parent["parse"] == PARSE_PLAIN:
                # A bare code column must never repeat the main cell, and it
                # must never carry "CODE - NAME". OTC parents legitimately do
                # both, 80 OTC 4 rows share their OTC 3 name on purpose.
                if parent_text == main_clean or " - " in parent_text:
                    noise_parent = True
                    break
            if parent["parse"] == PARSE_PLAIN:
                parents[parent["dim"]] = parent_text
            else:
                parent_code, parent_name = split_code_name(value, parent["parse"])
                parents[parent["dim"]] = parent_code if parent["on"] == "code" else parent_name

        if noise_parent:
            rows_noise += 1
            continue

        if cfg["parse"] == PARSE_ETHSTAT:
            name = build_ethstat_name(main_value, parents.get("ethgrp", ""))

        match_value = (code if cfg["match"] == "code" else name).upper()

        # One pack carries many quarters, the quarter is part of its identity
        if cfg["parse"] == PARSE_ITMA:
            for column, values in raw_items:
                if normalize_header(str(column)) == "QUARTER":
                    match_value = f"{match_value}_{clean_text(values[index]).upper()}"
                    break

        # One pack name can be sold by several companies, dedupe must keep them
        if cfg["parse"] == PARSE_PACK:
            for column, values in raw_items:
                if normalize_header(str(column)) == "PRODUCT":
                    match_value = f"{match_value}||{clean_text(values[index]).upper()}"
                    break

        if not match_value:
            rows_noise += 1
            continue

        if match_value in seen:
            rows_duplicate += 1
            continue
        seen.add(match_value)

        rows.append(
            {
                "code": code,
                "name": name,
                "match": match_value,
                "slug": build_slug(name),
                "parents": parents,
                "raw": {
                    str(key): ("" if is_blank(values[index])
                               else clean_text(values[index]))
                    for key, values in raw_items
                },
            }
        )
    return {
        "error": None,
        "dimension": dim_key,
        "part": part,
        "header_row": header_row,
        "columns": [str(c) for c in df.columns],
        "code_source": "column" if code_col else "name",
        "rows": rows,
        "rows_read": rows_read,
        "rows_clean": len(rows),
        "rows_noise": rows_noise,
        "rows_duplicate": rows_duplicate,
        "code_mismatch": code_mismatch,
    }

# Columns hidden from the raw data table, archive metadata only
SKIP_COLUMNS = {"deleted", "dat", "dby_id"}

# Leading columns, in this order
HEAD_ORDER = ["id", "code", "name"]

# Trailing columns, in this order
TAIL_ORDER = ["status", "cat", "uat", "cby_id", "uby_id"]

COLUMN_LABELS = {
    "id": "ID",
    "code": "Code",
    "slug": "Slug",
    "description": "Description",
    "remark": "Remark",
    "initial": "Initial",
    "shortname": "Shortname",
    "status": "Status",
    "cat": "Created At",
    "uat": "Updated At",
    "cby_id": "Created By",
    "uby_id": "Updated By",
    "key": "Key",
    "size": "Size",
    "strength": "Strength",
    "volume": "Volume",
    "launched": "Launched",
    "molstring": "Molecule String",
    "quarter": "Quarter",
    "unit": "Unit",
    "valuehna": "Value HNA",
    "date": "Date",
    "year": "Year",
}


# Translation key per model field, absent means keep the derived title
COLUMN_KEYS = {
    "id": "col_id", "code": "col_code", "slug": "col_slug",
    "description": "col_description", "remark": "col_remark",
    "initial": "col_initial", "shortname": "col_shortname",
    "status": "col_status", "cat": "col_created_at", "uat": "col_updated_at",
    "cby_id": "col_created_by", "uby_id": "col_updated_by",
    "key": "col_key", "size": "col_size", "strength": "col_strength",
    "volume": "col_volume", "launched": "col_launched",
    "molstring": "col_molecule_string", "quarter": "col_quarter",
    "unit": "col_unit", "valuehna": "col_value_hna",
    "date": "col_date", "year": "col_year",
}


# Readable label for a model field
def column_label(attname, cfg):
    if attname == "name":
        return cfg["label"]
    if attname in COLUMN_KEYS:
        return tr(COLUMN_KEYS[attname], COLUMN_LABELS.get(attname, attname))
    if attname in COLUMN_LABELS:
        return COLUMN_LABELS[attname]
    return attname.replace("_id", "").replace("_", " ").title()


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_display_columns                                 ║
# ║  Type: Service function                                    ║
# ║  Purpose: Full column layout, mirrors the database table   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/28-2026 by Akram                             ║
# ║  Updates: Aug/28-2026 by Akram, full column set            ║
# ╚════════════════════════════════════════════════════════════╝
# type drives the renderer, fk resolves to the related row name
def get_display_columns(dim_key):
    cfg = get_import_dimension(dim_key)
    parent_labels = {
        p["field"]: dim_label(p["dim"], IMPORT_DIMENSIONS[p["dim"]]["label"])
        for p in cfg["parents"]
    }
    # The name column is headed by the dimension itself, so it follows its label
    own_label = dim_label(dim_key, cfg["label"])
    available = [f.attname for f in cfg["model"]._meta.concrete_fields]

    def make(attname):
        if attname in parent_labels:
            return {"key": attname, "label": parent_labels[attname], "type": "fk"}
        if attname == "name":
            return {"key": attname, "label": own_label, "type": "text"}
        if attname in ("cby_id", "uby_id"):
            return {"key": attname, "label": column_label(attname, cfg), "type": "user"}
        if attname in ("cat", "uat", "launched", "date"):
            return {"key": attname, "label": column_label(attname, cfg), "type": "date"}
        if attname == "status":
            return {"key": attname, "label": tr("col_status", "Status"),
                    "type": "status"}
        return {"key": attname, "label": column_label(attname, cfg), "type": "text"}

    head = [make(f) for f in HEAD_ORDER if f in available]
    parents = [make(p["field"]) for p in cfg["parents"] if p["field"] in available]

    used = set(HEAD_ORDER) | set(TAIL_ORDER) | set(parent_labels) | SKIP_COLUMNS
    body = [make(f) for f in available if f not in used]
    tail = [make(f) for f in TAIL_ORDER if f in available]

    return head + parents + body + tail

# FK accessor name on the model, "corporation_id" becomes "corporation"
def relation_name(field_name):
    return field_name[:-3] if field_name.endswith("_id") else field_name

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: detect_dimensions                                   ║
# ║  Type: Service function                                    ║
# ║  Purpose: Every dimension a single file can feed           ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# IQVIA exports one pivot with many levels, ATC1 carries ATC2 and ATC3 too
# Dimension keys inside one classification family
def get_family_dimensions(family_key):
    return [
        key for key, sub in IMPORT_SUBGROUP.items()
        if sub == family_key
    ]


# What a picker choice maps to, a family expands to its members
def resolve_import_targets(dim_key):
    if dim_key in IMPORT_DIMENSIONS:
        return [dim_key]
    members = get_family_dimensions(dim_key)
    members.sort(key=lambda k: IMPORT_DIMENSIONS[k]["level"])
    return members


# ╔════════════════════════════════════════════════════════════╗
# ║  Name: detect_dimensions                                   ║
# ║  Type: Service function                                    ║
# ║  Purpose: Which of the chosen targets this file can feed   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_import_service.py     ║
# ║  Created: Aug/31-2026 by Akram                             ║
# ║  Updates: Aug/31-2026 by Akram, scoped to the user pick    ║
# ╚════════════════════════════════════════════════════════════╝
# Never scans outside the target list, a Pack file must not look like Corp
def detect_dimensions(raw_bytes, file_type, dim_key):
    targets = resolve_import_targets(dim_key)
    if not targets:
        return [], tr("err_unknown_dimension")

    raw_df, error = read_dataframe(raw_bytes, file_type)
    if error:
        return [], error

    header_row = None
    columns = []
    for index in range(min(HEADER_SCAN_ROWS, len(raw_df))):
        cells = [clean_text(v) for v in raw_df.iloc[index].tolist() if not is_blank(v)]
        normalized = {normalize_header(c) for c in cells}
        for key in targets:
            if normalize_header(IMPORT_DIMENSIONS[key]["main_col"]) in normalized:
                header_row = index
                columns = cells
                break
        if header_row is not None:
            break

    if header_row is None:
        wanted = ", ".join(IMPORT_DIMENSIONS[k]["main_col"] for k in targets)
        return [], tr_format("err_header_not_found_any", {"columns": wanted})

    present = {normalize_header(c) for c in columns}

    # A parent column can share a main_col name, OTC3.xlsx carries "OTC2".
    # Requiring the parents too keeps that file from claiming to hold OTC 2.
    # Pack and ITMA arrive as slices, one file never holds every parent.
    found = []
    for key in targets:
        cfg = IMPORT_DIMENSIONS[key]
        if normalize_header(cfg["main_col"]) not in present:
            continue
        if cfg["parse"] in (PARSE_PACK, PARSE_ITMA):
            found.append(key)
            continue
        needed = [p["column"] for p in cfg["parents"]]
        if cfg["code_col"]:
            needed.append(cfg["code_col"])
        if all(normalize_header(c) in present for c in needed):
            found.append(key)

    found.sort(key=lambda k: IMPORT_DIMENSIONS[k]["level"])
    return found, None