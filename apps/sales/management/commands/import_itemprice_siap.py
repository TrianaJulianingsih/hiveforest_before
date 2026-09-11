# import_itemprice_siap.py
#
# DIPULIHKAN 2026-08-21 dari bytecode (__pycache__/import_itemprice_siap.cpython-314.pyc).
# File .py aslinya hilang permanen: tidak ada di working tree, tidak ada di stash
# manapun, dan tidak pernah di-commit (sudah dicek via git log --all / rev-list).
# Struktur, nama fungsi, urutan validasi, format string, dan konstanta di bawah
# ini diambil persis dari disassembly, sehingga perilakunya sama dengan versi
# yang dulu dipakai.
#
# CATATAN PENTING SEBELUM DIPAKAI ULANG:
#
# 1. SKIP_SOURCE_INDICES di bawah berbasis INDEX DataFrame (posisi), bukan
#    kode produk. Kalau file sumber dibangun ulang / berubah urutannya, tiga
#    index ini akan melewati baris yang BERBEDA dari yang dimaksud semula.
#    handle() mencetak index apa saja yang dilewati -- periksa outputnya.
#
# 2. _required_date memanggil pd.to_datetime(text, errors="coerce") TANPA
#    dayfirst/format. Kalau kolom `tanggal` berupa teks DD/MM/YYYY, tanggal
#    dengan hari <= 12 bisa terbaca sebagai MM/DD/YYYY tanpa error.
#
# 3. Default-nya INSERT-ONLY. Kalau `code` sudah ada di DB dengan HJP sama
#    -> row di-skip; kalau HJP berbeda -> seluruh import dibatalkan
#    (CommandError). Tambahan 2026-08-21: flag --update-existing membuat
#    baris yang HJP-nya berbeda DITIMPA (hna, hjp, uat, uby) memakai
#    queryset.update() -- sengaja tidak lewat .save() supaya tidak memicu
#    full_clean()/regenerasi slug pada baris lama.
#    Karena `code` memuat tanggal effective, memperbaiki effective tetap
#    menghasilkan code baru -> baris lama TIDAK tergantikan oleh flag ini,
#    itu kasus terpisah yang harus dibersihkan manual.
#
# 4. `--cby` hanya dipakai untuk memvalidasi bahwa user-nya ada; field `cby`
#    pada ItemPrice tidak diisi (sesuai bytecode aslinya).

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.finance.models.products import ItemPrice
from apps.sales.models.sales import SalesType
from apps.supplychain.models.distributions import Distributor, DistributorItem


class Command(BaseCommand):
    help = (
        "Strict insert ItemPrice dari file SIAP. Distributor, DistributorItem, "
        "dan SalesType wajib berhasil di-resolve."
    )

    REQUIRED_COLUMNS = frozenset(
        {
            "kode_distributor",
            "kode_produk",
            "sector",
            "kode_sector",
            "nama_produk",
            "tanggal",
            "hna",
            "hjp",
        }
    )

    SKIP_SOURCE_INDICES = frozenset({354, 355, 642})

    def add_arguments(self, parser):
        parser.add_argument("--file", help="Path file CSV/XLSX SIAP.")
        parser.add_argument("--cby", type=int, help="User ID yang melakukan insert.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validasi tanpa menulis data ke database.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help=(
                "Kalau code sudah ada di DB dengan HJP berbeda, TIMPA hna/hjp-nya "
                "dengan nilai dari file (default: batalkan import)."
            ),
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        cby_id = options["cby"]
        dry_run = options["dry_run"]
        update_existing = options["update_existing"]

        if not file_path.exists():
            raise CommandError(f"File tidak ditemukan: {file_path}")

        try:
            user = get_user_model().objects.get(id=cby_id)
        except get_user_model().DoesNotExist:
            raise CommandError(f"User dengan ID {cby_id} tidak ditemukan.")

        dataframe = self._read_file(file_path)
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

        duplicate_columns = dataframe.columns[dataframe.columns.duplicated()].tolist()
        if duplicate_columns:
            raise CommandError(f"Ada kolom duplicate: {', '.join(sorted(duplicate_columns))}")

        missing_columns = self.REQUIRED_COLUMNS - set(dataframe.columns)
        if missing_columns:
            raise CommandError(
                f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing_columns))}"
            )

        self.stdout.write(f"File: {file_path}")
        self.stdout.write(f"Rows: {len(dataframe)}")

        lookups = self._load_lookups()

        skipped_source_indices = set()
        prepared, errors = self._prepare_rows(dataframe, lookups, skipped_source_indices)

        if skipped_source_indices:
            self.stdout.write(
                self.style.WARNING(
                    "Row berdasarkan index DataFrame yang dilewati: "
                    + ", ".join(map(str, sorted(skipped_source_indices)))
                )
            )

        if errors:
            self._print_errors(errors)
            self.stdout.write(
                self.style.WARNING(f"{len(errors)} row dilewati karena gagal validasi.")
            )

        if not prepared:
            raise CommandError("Tidak ada row valid untuk diproses.")

        prepared, collapsed = self._collapse_identical_duplicates(prepared)
        collapsed_row_count = sum(len(dropped) for _, _, dropped in collapsed)
        if collapsed:
            self.stdout.write(
                self.style.WARNING(
                    f"{collapsed_row_count} row digabung karena code sama dan HNA/HJP identik:"
                )
            )
            for code, kept_index, dropped_indices in collapsed:
                self.stdout.write(
                    f"  - {code}: pakai idx {kept_index}, "
                    f"buang idx {', '.join(map(str, dropped_indices))}"
                )

        skipped_existing_codes, different_hjp_codes = self._validate_code_duplicates(
            prepared, update_existing=update_existing
        )
        if skipped_existing_codes:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(skipped_existing_codes)} row dilewati karena code sudah ada dan HJP sama."
                )
            )
        if different_hjp_codes:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(different_hjp_codes)} row akan DITIMPA hna/hjp-nya (--update-existing)."
                )
            )

        # Baris ber-code yang sudah ada di DB tidak boleh di-INSERT lagi:
        # yang HJP-nya sama -> dilewati, yang berbeda -> di-UPDATE di bawah.
        to_update = {
            item.code: item for item in prepared if item.code in set(different_hjp_codes)
        }
        prepared = [
            item
            for item in prepared
            if item.code not in skipped_existing_codes and item.code not in to_update
        ]
        total_skipped = (
            len(errors)
            + len(skipped_existing_codes)
            + len(skipped_source_indices)
            + collapsed_row_count
        )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DRY-RUN OK: {len(prepared)} row valid; {len(to_update)} row akan di-update; "
                    f"{total_skipped} row dilewati; tidak ada data yang ditulis."
                )
            )
            message = (
                f"DRY-RUN: {len(prepared)} valid, {total_skipped} skipped, "
                f"0 inserted, {len(to_update)} would-update"
            )
            self.stdout.write(message)
            return

        with transaction.atomic():
            for item in prepared:
                item.save()
            for code, item in to_update.items():
                # Pakai queryset.update() supaya tidak memicu ItemPrice.save()
                # (full_clean + regenerasi slug) pada baris lama.
                ItemPrice.objects.filter(code=code).update(
                    hna=item.hna, hjp=item.hjp, uat=timezone.now(), uby=user
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import selesai: {len(prepared)} row inserted, "
                f"{len(to_update)} row updated, {total_skipped} row skipped."
            )
        )
        self.stdout.write(
            f"{len(prepared)} inserted, {len(to_update)} updated, {total_skipped} skipped"
        )

    def _read_file(self, file_path):
        extension = file_path.suffix.lower()
        if extension == ".csv":
            return pd.read_csv(str(file_path), dtype=str, keep_default_na=False)
        if extension in (".xlsx", ".xls"):
            return pd.read_excel(str(file_path), dtype=str, keep_default_na=False)
        raise CommandError("Format file harus .csv, .xlsx, atau .xls.")

    def _load_lookups(self):
        return {
            "distributors": self._make_lookup(
                Distributor.nondeleted_objects.all(), "initial"
            ),
            "distitems": self._make_lookup(
                DistributorItem.nondeleted_objects.all(), "code"
            ),
            "salestypes": self._make_lookup(SalesType.nondeleted_objects.all(), "name"),
        }

    def _make_lookup(self, queryset, field_name):
        lookup = {}
        for obj in queryset:
            key = self._normalize_key(getattr(obj, field_name))
            lookup.setdefault(key, []).append(obj)
        return lookup

    def _prepare_rows(self, dataframe, lookups, skipped_source_indices):
        prepared = []
        errors = []
        for source_index, row in dataframe.iterrows():
            if source_index in self.SKIP_SOURCE_INDICES:
                skipped_source_indices.add(source_index)
                continue

            row_number = int(source_index) + 2
            try:
                item = self._prepare_item(row, lookups)
                item._source_index = source_index
                prepared.append(item)
            except (CommandError, ValidationError, ValueError, TypeError) as error:
                errors.append(f"row {row_number}: {error}")
        return prepared, errors

    def _prepare_item(self, row, lookups):
        distributor = self._resolve_required(
            row.get("kode_distributor"),
            lookups["distributors"],
            "Distributor.initial",
            "kode_distributor",
        )
        distitem = self._resolve_required(
            row.get("kode_produk"),
            lookups["distitems"],
            "DistributorItem.code",
            "kode_produk",
        )
        salestype = self._resolve_required(
            row.get("sector"),
            lookups["salestypes"],
            "SalesType.name",
            "sector",
        )

        name = self._required_text(row.get("nama_produk"), "nama_produk")
        effective = self._required_date(row.get("tanggal"), "tanggal")
        hna = self._required_decimal(row.get("hna"), "hna")
        hjp = self._required_decimal(row.get("hjp"), "hjp")

        distributor_code = self._required_text(distributor.code, "Distributor.code")
        salestype_code = self._required_text(salestype.code, "SalesType.code")
        distitem_code = self._required_text(distitem.code, "DistributorItem.code")

        code = (
            f"{distributor_code} {salestype_code} {distitem_code} "
            f"{effective.strftime('%Y%m%d')}"
        )

        item = ItemPrice(
            code=code,
            name=name,
            description=None,
            remark=None,
            status=1,
            distributor=distributor,
            distitem=distitem,
            salestype=salestype,
            hna=hna,
            hjp=hjp,
            pct_pm=None,
            pct_advdisc=None,
            effective=effective,
            priceuom=None,
            conversionsize=None,
        )
        return item

    def _resolve_required(self, value, lookup, target_label, source_label):
        source_value = self._required_text(value, source_label)
        key = self._normalize_key(source_value)
        matches = lookup.get(key)

        if not matches:
            raise CommandError(
                f"{target_label} tidak ditemukan untuk {source_label}={source_value}."
            )
        if len(matches) > 1:
            ids = ", ".join(str(obj.id) for obj in matches)
            raise CommandError(
                f"{target_label} duplicate untuk {source_label}={source_value}; id={ids}."
            )
        return matches[0]

    def _collapse_identical_duplicates(self, items):
        """Gabungkan baris yang menghasilkan `code` sama PADAHAL hna+hjp-nya identik.

        Terjadi ketika beberapa id_produk_oi di sumber menunjuk DistributorItem
        yang sama, sehingga kombinasi (distributor, salestype, item, effective)
        bertabrakan tanpa ada perbedaan harga sama sekali. Contoh nyata:
        `MU SP KN3BAK 20150102` muncul di idx 207 & 242 -- beda id_pricelist /
        id_produk_oi / nama_produk / kode_team / last_update, tapi hjp & hna
        persis sama.

        Kalau hna/hjp-nya BERBEDA, baris TIDAK digabung: dibiarkan lolos ke
        _validate_code_duplicates supaya import ditolak, karena memilih salah
        satu harga adalah keputusan manusia, bukan tebakan script.

        Mengembalikan (items_yang_dipakai, daftar_collapsed) dengan
        daftar_collapsed berisi tuple (code, index_yang_dipakai, [index_dibuang]).
        """
        by_code = {}
        for item in items:
            by_code.setdefault(item.code, []).append(item)

        kept = []
        collapsed = []
        for code, group in by_code.items():
            if len(group) == 1:
                kept.append(group[0])
                continue

            distinct_prices = {(item.hna, item.hjp) for item in group}
            if len(distinct_prices) > 1:
                # Harga berbeda -> bukan duplikat. Biarkan validasi berikutnya menolak.
                kept.extend(group)
                continue

            group_sorted = sorted(group, key=lambda item: item._source_index)
            kept.append(group_sorted[0])
            collapsed.append(
                (
                    code,
                    group_sorted[0]._source_index,
                    [item._source_index for item in group_sorted[1:]],
                )
            )

        kept.sort(key=lambda item: item._source_index)
        return kept, collapsed

    def _validate_code_duplicates(self, items, update_existing=False):
        codes = Counter(item.code for item in items)

        prepared_by_code = {}
        for item in items:
            prepared_by_code.setdefault(item.code, []).append(item)

        duplicate_codes = sorted(code for code, count in codes.items() if count > 1)
        if duplicate_codes:
            duplicate_row_count = sum(codes[code] for code in duplicate_codes)
            duplicate_extra_row_count = duplicate_row_count - len(duplicate_codes)
            duplicate_index_details = "; ".join(
                f"{code} -> idx "
                + ", ".join(str(item._source_index) for item in prepared_by_code[code])
                for code in duplicate_codes
            )
            raise CommandError(
                f"code duplicate di file: {len(duplicate_codes)} code, "
                f"{duplicate_row_count} row terlibat "
                f"({duplicate_extra_row_count} row ekstra). "
                f"Detail index: {duplicate_index_details}"
            )

        existing_codes = set(codes)
        existing_hjp = dict(
            ItemPrice.objects.filter(code__in=existing_codes).values_list("code", "hjp")
        )

        same_hjp_codes = set()
        different_hjp_codes = []

        if existing_hjp:
            self.stderr.write("Perbandingan HJP source vs database:")
            for code in sorted(existing_hjp):
                source_hjp = prepared_by_code[code][0].hjp
                database_hjp = existing_hjp[code]
                if source_hjp == database_hjp:
                    status = "SAMA"
                    same_hjp_codes.add(code)
                else:
                    status = "BEDA"
                    different_hjp_codes.append(code)
                self.stderr.write(
                    f"- {code}: source={source_hjp}, database={database_hjp}, {status}"
                )

        if different_hjp_codes and not update_existing:
            examples = ", ".join(sorted(different_hjp_codes))
            raise CommandError(
                "code sudah ada dengan HJP berbeda di finance_itemprice "
                f"({len(different_hjp_codes)} row): {examples}. "
                "Pakai --update-existing kalau nilai dari file memang harus menimpa DB."
            )

        return same_hjp_codes, different_hjp_codes

    @staticmethod
    def _normalize_key(value):
        return str(value).strip().upper()

    def _required_text(self, value, field_name):
        if pd.isna(value):
            raise CommandError(f"{field_name} kosong.")
        text = str(value).strip()
        if not text or text.upper() in {"NAN", "NULL", "<NA>", "NONE"}:
            raise CommandError(f"{field_name} kosong.")
        return text

    def _required_decimal(self, value, field_name):
        text = self._required_text(value, field_name)
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            raise CommandError(f"{field_name} bukan decimal yang valid: {text}.")

    def _required_date(self, value, field_name):
        text = self._required_text(value, field_name)
        parsed = pd.to_datetime(text, errors="coerce")
        if pd.isna(parsed):
            raise CommandError(f"{field_name} bukan tanggal yang valid: {text}.")
        return parsed.date()

    def _print_errors(self, errors):
        self.stderr.write("Detail error validasi:")
        for error in errors[:20]:
            self.stderr.write(f"- {error}")
        if len(errors) > 20:
            self.stderr.write(f"... dan {len(errors) - 20} error lainnya.")
