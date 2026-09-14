# Utandra | Export rekonsiliasi Selling Out -> Excel (pivot grup produk x bulan).
#
# TAHAP 1: baru tabel SUMBER SellingOut. Sumber lain (DO MUP, RawMUSO) + tabel
# selisih (value & %) menyusul setelah pemetaan grup produk untuk sumber-sumber
# itu final.
#
# Layout tiap sheet (1 sheet per TAHUN):
#   A1 = tahun ; B1..M1 = JAN..DEC ; kolom TOTAL (sum horizontal per grup)
#   baris = grup produk ; baris terakhir TOTAL (sum vertikal per bulan)
#
# Grup produk (rantai FK, sesuai arahan):
#   sales_sellingout.item_id -> supplychain_distributoritem.product_id
#     -> sales_product.subgroup_id -> sales_productsubgroup.group_id
#     -> sales_productgroup.code

from datetime import datetime
from io import BytesIO

import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import HttpResponse, HttpResponseBadRequest

DISTRIBUTOR_ID = 1
MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]

# metrik -> kolom di sales_sellingout
SO_METRIC = {"qty": "qty", "thna": "grossvalue"}

# label baris untuk row yang grup produknya tidak ketemu (rantai FK putus)
NO_GROUP = "(TANPA GRUP)"


@staff_member_required
def export_so_reconciliation(request):
    metric = request.GET.get("metric", "qty")
    if metric not in SO_METRIC:
        return HttpResponseBadRequest("metric harus 'qty' atau 'thna'.")

    def _parse(name):
        try:
            return datetime.strptime(request.GET.get(name, "").strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    date_from = _parse("date_from")
    date_to = _parse("date_to")
    if not (date_from and date_to):
        return HttpResponseBadRequest("date_from & date_to wajib (format YYYY-MM-DD).")
    if date_from > date_to:
        return HttpResponseBadRequest("date_from tidak boleh setelah date_to.")

    col = SO_METRIC[metric]
    # LEFT JOIN: baris yang rantai grup produknya putus (item/product/subgroup/
    # group null) tetap ikut, dikumpulkan di label fallback -> tidak hilang.
    sql = f"""
        SELECT COALESCE(NULLIF(TRIM(pg.code), ''), '{NO_GROUP}') AS grup,
               EXTRACT(YEAR  FROM ss.invoice_date)::int AS thn,
               EXTRACT(MONTH FROM ss.invoice_date)::int AS bln,
               COALESCE(SUM(ss.{col}), 0)::float8 AS val
        FROM sales_sellingout ss
        LEFT JOIN supplychain_distributoritem di ON di.id  = ss.item_id
        LEFT JOIN sales_product p                ON p.id   = di.product_id
        LEFT JOIN sales_productsubgroup psg      ON psg.id = p.subgroup_id
        LEFT JOIN sales_productgroup pg          ON pg.id  = psg.group_id
        WHERE ss.distributor_id = %s
          AND ss.invoice_date BETWEEN %s AND %s
          AND ss.status = 1 AND ss.deleted = false
          AND p.business_id = 2
        GROUP BY 1, 2, 3
        ORDER BY 2, 1, 3
    """
    with connection.cursor() as cur:
        cur.execute(sql, [DISTRIBUTOR_ID, date_from, date_to])
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=["grup", "thn", "bln", "val"])

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if df.empty:
            pd.DataFrame(
                {"info": ["Tidak ada data untuk rentang & filter ini."]}
            ).to_excel(writer, sheet_name="SellingOut", index=False)
        else:
            for year, g in df.groupby("thn"):
                pivot = g.pivot_table(
                    index="grup", columns="bln", values="val",
                    aggfunc="sum", fill_value=0,
                )
                pivot = pivot.reindex(columns=range(1, 13), fill_value=0)
                pivot.columns = MONTHS
                pivot["TOTAL"] = pivot.sum(axis=1)           # sum horizontal
                pivot.loc["TOTAL"] = pivot.sum(axis=0)        # sum vertikal
                pivot.index.name = str(int(year))             # A1 = tahun
                pivot.to_excel(writer, sheet_name=f"SellingOut {int(year)}")

    resp = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    fname = f"rekonsiliasi_sellingout_{metric}_{date_from}_{date_to}.xlsx"
    resp["Content-Disposition"] = f'attachment; filename="{fname}"'
    return resp
