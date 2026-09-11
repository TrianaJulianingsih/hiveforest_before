from django import template

register = template.Library()

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: is_active                                           ║
# ║  Type: Simple template tag                                 ║
# ║  Purpose: To filter active map in region province          ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\templatetags\sales_tag.py                ║
# ║  Created: Jul/5-2025 by Setiadji                           ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@register.simple_tag
def is_active(province_id, region_id, active_map):
    return (province_id, region_id) in active_map

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: is_shared                                           ║
# ║  Type: Simple template tag                                 ║
# ║  Purpose: To filter if active map is shared                ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\templatetags\sales_tag.py                ║
# ║  Created: Jul/5-2025 by Setiadji                           ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@register.simple_tag
def is_shared(province_id, shared_ids):
    return province_id in shared_ids

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_region_mapping                                  ║
# ║  Type: Simple template tag                                 ║
# ║  Purpose: To get mapping dictionary for regency matrix     ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\templatetags\sales_tag.py                ║
# ║  Created: Jul/7-2025 by Setiadji                           ║
# ║  Updates: Jul/13-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝
@register.simple_tag
def get_region_mapping(mapping_dict, province_id, region_id):
    return mapping_dict.get((province_id, region_id))

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_area_mapping                                    ║
# ║  Type: Simple template tag                                 ║
# ║  Purpose: To get mapping dictionary for area matrix        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\templatetags\sales_tag.py                ║
# ║  Created: Jul/13-2025 by Setiadji                          ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@register.simple_tag
def get_area_mapping(mapping_dict, regency_id, area_id):
    return mapping_dict.get((regency_id, area_id))

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: get_item                                            ║
# ║  Type: Simple template tag                                 ║
# ║  Purpose: To get mapping dictionary for area matrix        ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\sales\templatetags\sales_tag.py                ║
# ║  Created: Jul/19-2025 by Setiadji                          ║
# ║  Updates: ? by Setiadji                                    ║
# ╚════════════════════════════════════════════════════════════╝
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])