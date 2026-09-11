from apps.analytics.models.iqvia import (
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

# Dimension above this row count needs typed keyword first
BIG_ROWS = 500
SEARCH_MIN_CHARS = 3

# Period basis options for X axis
PERIOD_YEAR = "year"
PERIOD_QUARTER = "quarter"
PERIOD_MAT = "mat"

# MAT sums the current quarter plus the three before it
MAT_WINDOW = 4

# Measure options for Y value
MEASURE_VALUE = "valuehna"
MEASURE_UNIT = "unit"

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: DIMENSIONS                                          ║
# ║  Type: Constant registry                                   ║
# ║  Purpose: Master map of every filterable IQVIA dimension   ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\analytics\services\iqvia_dimension_service.py  ║
# ║  Created: Aug/20-2026 by Akram                             ║
# ║  Updates: ?                                                ║
# ╚════════════════════════════════════════════════════════════╝
# key       : id used in query string
# label     : text shown to user
# model     : source model for option list
# family    : cascade group
# level     : position inside family, 1 is top
# parent    : key of one level above, None if top
# pack_path : ORM path counted from IQV_Pack, empty means Pack itself
# big       : True if row count is above BIG_ROWS
DIMENSIONS = {
    # Corporation family
    "corp": {
        "label": "Corporation",
        "model": IQV_Corp,
        "family": "corporation",
        "level": 1,
        "parent": None,
        "pack_path": "product__company__corporation",
        "big": True,
    },
    "company": {
        "label": "Company",
        "model": IQV_Company,
        "family": "corporation",
        "level": 2,
        "parent": "corp",
        "pack_path": "product__company",
        "big": True,
    },
    "product": {
        "label": "Product",
        "model": IQV_Product,
        "family": "product",
        "level": 1,
        "parent": "company",
        "pack_path": "product",
        "big": True,
    },
    "pack": {
        "label": "Pack",
        "model": IQV_Pack,
        "family": "product",
        "level": 2,
        "parent": "product",
        "pack_path": "",
        "big": True,
    },
    # ATC family
    "atc1": {
        "label": "ATC 1",
        "model": IQV_ATC1,
        "family": "atc",
        "level": 1,
        "parent": None,
        "pack_path": "atc4__atc3__atc2__atc1",
        "big": False,
    },
    "atc2": {
        "label": "ATC 2",
        "model": IQV_ATC2,
        "family": "atc",
        "level": 2,
        "parent": "atc1",
        "pack_path": "atc4__atc3__atc2",
        "big": False,
    },
    "atc3": {
        "label": "ATC 3",
        "model": IQV_ATC3,
        "family": "atc",
        "level": 3,
        "parent": "atc2",
        "pack_path": "atc4__atc3",
        "big": False,
    },
    "atc4": {
        "label": "ATC 4",
        "model": IQV_ATC4,
        "family": "atc",
        "level": 4,
        "parent": "atc3",
        "pack_path": "atc4",
        "big": True,
    },
    # OTC family
    "otc1": {
        "label": "OTC 1",
        "model": IQV_OTC1,
        "family": "otc",
        "level": 1,
        "parent": None,
        "pack_path": "otc4__otc3__otc2__otc1",
        "big": False,
    },
    "otc2": {
        "label": "OTC 2",
        "model": IQV_OTC2,
        "family": "otc",
        "level": 2,
        "parent": "otc1",
        "pack_path": "otc4__otc3__otc2",
        "big": False,
    },
    "otc3": {
        "label": "OTC 3",
        "model": IQV_OTC3,
        "family": "otc",
        "level": 3,
        "parent": "otc2",
        "pack_path": "otc4__otc3",
        "big": False,
    },
    "otc4": {
        "label": "OTC 4",
        "model": IQV_OTC4,
        "family": "otc",
        "level": 4,
        "parent": "otc3",
        "pack_path": "otc4",
        "big": True,
    },
    # NFC family
    "nfc1": {
        "label": "NFC 1",
        "model": IQV_NFC1,
        "family": "nfc",
        "level": 1,
        "parent": None,
        "pack_path": "nfc3__nfc2__nfc1",
        "big": False,
    },
    "nfc2": {
        "label": "NFC 2",
        "model": IQV_NFC2,
        "family": "nfc",
        "level": 2,
        "parent": "nfc1",
        "pack_path": "nfc3__nfc2",
        "big": False,
    },
    "nfc3": {
        "label": "NFC 3",
        "model": IQV_NFC3,
        "family": "nfc",
        "level": 3,
        "parent": "nfc2",
        "pack_path": "nfc3",
        "big": False,
    },
    # Brand family
    "genflag": {
        "label": "Generic Flag",
        "model": IQV_GenFlag,
        "family": "brand",
        "level": 1,
        "parent": None,
        "pack_path": "branddet__gen_flag",
        "big": False,
    },
    "branddet": {
        "label": "Brand Detail",
        "model": IQV_BrandDet,
        "family": "brand",
        "level": 2,
        "parent": "genflag",
        "pack_path": "branddet",
        "big": False,
    },
    # Ethical family
    "ethgrp": {
        "label": "Ethical Status Group",
        "model": IQV_EthStatGrp,
        "family": "ethical",
        "level": 1,
        "parent": None,
        "pack_path": "ethstatgrp",
        "big": False,
    },
    "ethstat": {
        "label": "Ethical Status",
        "model": IQV_EthStat,
        "family": "ethical",
        "level": 2,
        "parent": "ethgrp",
        "pack_path": "ethstat",
        "big": False,
    },
    # Standalone attributes
    "comtype": {
        "label": "Company Type",
        "model": IQV_ComType,
        "family": "corporation",
        "level": 3,
        "parent": None,
        "pack_path": "product__company__comtype",
        "big": False,
    },
    "packform": {
        "label": "Pack Form",
        "model": IQV_PackForm,
        "family": "product",
        "level": 3,
        "parent": None,
        "pack_path": "form",
        "big": True,
    },
    "regstat": {
        "label": "Registration Status",
        "model": IQV_RegStat,
        "family": "product",
        "level": 4,
        "parent": None,
        "pack_path": "regstat",
        "big": False,
    },
}

FAMILY_LABELS = {
    "corporation": "Corporation",
    "product": "Product",
    "atc": "ATC",
    "otc": "OTC",
    "nfc": "NFC",
    "brand": "Brand",
    "ethical": "Ethical Status",
}


# Dimension config, None when key is unknown
def get_dimension(key):
    return DIMENSIONS.get(key)


# True when key is a registered dimension
def is_valid_dimension(key):
    return key in DIMENSIONS


# ORM path counted from IQV_ITMATrans
def trans_path(key):
    pack_path = DIMENSIONS[key]["pack_path"]
    if not pack_path:
        return "pack"
    return f"pack__{pack_path}"


# ORM field prefix counted from IQV_Pack
def pack_prefix(key):
    pack_path = DIMENSIONS[key]["pack_path"]
    if not pack_path:
        return ""
    return f"{pack_path}__"


# Minimum typed chars before option list is served
def search_min_chars(key):
    return SEARCH_MIN_CHARS if DIMENSIONS[key]["big"] else 0


# Dimensions grouped by family, for the settings panel
def get_dimension_groups():
    groups = {}
    for key, cfg in DIMENSIONS.items():
        groups.setdefault(cfg["family"], []).append(
            {
                "key": key,
                "label": cfg["label"],
                "level": cfg["level"],
                "parent": cfg["parent"],
                "search_min": search_min_chars(key),
            }
        )
    result = []
    for family, items in groups.items():
        result.append(
            {
                "family": family,
                "label": FAMILY_LABELS.get(family, family),
                "items": sorted(items, key=lambda x: x["level"]),
            }
        )
    return result