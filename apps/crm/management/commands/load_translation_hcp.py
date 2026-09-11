import logging

from django.core.management.base import BaseCommand
from django.db import connection

# ═══════════════════════════════════════════════════════════
# FaisalS | HF CRM | Healthcare Professional: translation seed
# ═══════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


TRANSLATION_SEED_SQL = """
DO $$
DECLARE
  v_module_id integer;
  v_key_id integer;
  v_slug text;
  v_counter integer;
BEGIN
  -- === Module: hcp_list ===
  SELECT id INTO v_module_id FROM base_translation_module WHERE code = 'hcp_list';
  IF v_module_id IS NULL THEN
    v_slug := 'healthcare-professionals-list';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_module WHERE slug = v_slug) LOOP
      v_slug := 'healthcare-professionals-list' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_module (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, code) VALUES ('Healthcare Professionals - List', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, 'hcp_list') RETURNING id INTO v_module_id;
  END IF;

  -- key: hcp_list.btn_dashboard
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_dashboard';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_dashboard';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_dashboard' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_dashboard', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_dashboard', 'Dashboard') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_dashboard_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_dashboard_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_dashboard_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Dasbor');
  END IF;

  -- key: hcp_list.btn_export
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_export';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_export';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_export' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_export', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_export', 'Export') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_export_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_export_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_export_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Ekspor');
  END IF;

  -- key: hcp_list.btn_filter
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_filter';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_filter';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_filter', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_filter', 'Filter') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_filter_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_filter_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Filter');
  END IF;

  -- key: hcp_list.col_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_education';
  IF v_key_id IS NULL THEN
    v_slug := 'col_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_education', 'EDUCATION') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PENDIDIKAN');
  END IF;

  -- key: hcp_list.col_license
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_license';
  IF v_key_id IS NULL THEN
    v_slug := 'col_license';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_license' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_license', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_license', 'LICENSE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_license_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_license_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_license_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'LISENSI');
  END IF;

  -- key: hcp_list.col_name
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_name';
  IF v_key_id IS NULL THEN
    v_slug := 'col_name';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_name' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_name', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_name', 'NAME') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_name_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_name_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_name_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NAMA');
  END IF;

  -- key: hcp_list.col_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_no';
  IF v_key_id IS NULL THEN
    v_slug := 'col_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_no', 'NO') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NO');
  END IF;

  -- key: hcp_list.col_place_of_practice
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_place_of_practice';
  IF v_key_id IS NULL THEN
    v_slug := 'col_place_of_practice';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_place_of_practice', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_place_of_practice', 'PLACE OF PRACTICE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_place_of_practice_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_place_of_practice_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TEMPAT PRAKTIK');
  END IF;

  -- key: hcp_list.col_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_province';
  IF v_key_id IS NULL THEN
    v_slug := 'col_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_province', 'PROVINCE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_province_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'PROVINCE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PROVINSI');
  END IF;

  -- key: hcp_list.col_specialities
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_specialities';
  IF v_key_id IS NULL THEN
    v_slug := 'col_specialities';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_specialities', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_specialities', 'SPECIALITIES') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_specialities_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_specialities_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'SPECIALITIES');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_specialities_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_specialities_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'SPESIALISASI');
  END IF;

  -- key: hcp_list.col_start_date
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_start_date';
  IF v_key_id IS NULL THEN
    v_slug := 'col_start_date';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_start_date', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_start_date', 'START DATE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_start_date_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'START DATE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_start_date_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TANGGAL MULAI');
  END IF;

  -- key: hcp_list.col_status
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_status';
  IF v_key_id IS NULL THEN
    v_slug := 'col_status';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_status' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_status', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_status', 'STATUS') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_status_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_status_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_status_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'STATUS');
  END IF;

  -- key: hcp_list.empty_state
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_state';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_state';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_state' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_state', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_state', 'No healthcare professionals found.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_state_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_state_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_state_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada tenaga kesehatan yang ditemukan.');
  END IF;

  -- key: hcp_list.label_entries
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_entries';
  IF v_key_id IS NULL THEN
    v_slug := 'label_entries';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_entries' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_entries', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_entries', 'entries') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'label_entries_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'entries');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_entries_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'entri');
  END IF;

  -- key: hcp_list.label_in_total
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_in_total';
  IF v_key_id IS NULL THEN
    v_slug := 'label_in_total';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_in_total', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_in_total', 'in total') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_in_total_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_in_total_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'total');
  END IF;

  -- key: hcp_list.label_of
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_of';
  IF v_key_id IS NULL THEN
    v_slug := 'label_of';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_of' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_of', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_of', 'of') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_of_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_of_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_of_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'dari');
  END IF;

  -- key: hcp_list.label_results
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_results';
  IF v_key_id IS NULL THEN
    v_slug := 'label_results';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_results' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_results', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_results', 'results') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_results_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_results_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_results_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'hasil');
  END IF;

  -- key: hcp_list.label_show
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_show';
  IF v_key_id IS NULL THEN
    v_slug := 'label_show';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_show' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_show', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_show', 'Show') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_show_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_show_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_show_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Menampilkan');
  END IF;

  -- key: hcp_list.label_to
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_to';
  IF v_key_id IS NULL THEN
    v_slug := 'label_to';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_to' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_to', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_to', 'to') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_to_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_to_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_to_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'sampai');
  END IF;

  -- key: hcp_list.page_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'page_title';
  IF v_key_id IS NULL THEN
    v_slug := 'page_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'page_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('page_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'page_title', 'Healthcare Professionals') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'page_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'page_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('page_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tenaga Kesehatan');
  END IF;

  -- key: hcp_list.search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'search_placeholder', 'Search') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari');
  END IF;

  -- key: hcp_list.status_active
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'status_active';
  IF v_key_id IS NULL THEN
    v_slug := 'status_active';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'status_active' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('status_active', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'status_active', 'Active') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'status_active_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'status_active_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('status_active_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Aktif');
  END IF;

  -- key: hcp_list.status_inactive
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'status_inactive';
  IF v_key_id IS NULL THEN
    v_slug := 'status_inactive';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'status_inactive' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('status_inactive', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'status_inactive', 'Inactive') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'status_inactive_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'status_inactive_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('status_inactive_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak Aktif');
  END IF;

  -- === Module: hcp_analytics ===
  SELECT id INTO v_module_id FROM base_translation_module WHERE code = 'hcp_analytics';
  IF v_module_id IS NULL THEN
    v_slug := 'healthcare-professionals-analytics';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_module WHERE slug = v_slug) LOOP
      v_slug := 'healthcare-professionals-analytics' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_module (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, code) VALUES ('Healthcare Professionals - Analytics', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, 'hcp_analytics') RETURNING id INTO v_module_id;
  END IF;

  -- key: hcp_analytics.btn_back
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_back';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_back';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_back' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_back', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_back', 'Back') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_back_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_back_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_back_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kembali');
  END IF;

  -- key: hcp_analytics.btn_export
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_export';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_export';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_export' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_export', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_export', 'Export') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_export_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_export_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_export_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Ekspor');
  END IF;

  -- key: hcp_analytics.btn_filter
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_filter';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_filter';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_filter', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_filter', 'Filter') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_filter_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_filter_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Filter');
  END IF;

  -- key: hcp_analytics.chart_education_empty
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_education_empty';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_education_empty';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_education_empty' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_education_empty', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_education_empty', 'No education data available yet.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_education_empty_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_education_empty_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_education_empty_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Data pendidikan belum tersedia.');
  END IF;

  -- key: hcp_analytics.chart_education_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_education_title';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_education_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_education_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_education_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_education_title', 'Healthcare Education') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_education_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_education_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_education_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Pendidikan Tenaga Kesehatan');
  END IF;

  -- key: hcp_analytics.chart_places_empty
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_places_empty';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_places_empty';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_places_empty' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_places_empty', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_places_empty', 'No place-of-practice data available yet.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_places_empty_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_places_empty_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_places_empty_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Data tempat praktik belum tersedia.');
  END IF;

  -- key: hcp_analytics.chart_places_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_places_title';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_places_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_places_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_places_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_places_title', 'Top Hospitals / Places of Practice') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_places_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_places_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_places_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Rumah Sakit / Tempat Praktik Teratas');
  END IF;

  -- key: hcp_analytics.chart_province_empty
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_province_empty';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_province_empty';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_empty' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_province_empty', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_province_empty', 'No province data available yet.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_province_empty_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_empty_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_province_empty_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Data provinsi belum tersedia.');
  END IF;

  -- key: hcp_analytics.chart_province_subtitle
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_province_subtitle';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_province_subtitle';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_subtitle' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_province_subtitle', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_province_subtitle', 'Click or hover a province to see how many doctors practice there.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_province_subtitle_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_subtitle_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_province_subtitle_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Klik atau arahkan kursor ke provinsi untuk melihat jumlah dokter yang berpraktik di sana.');
  END IF;

  -- key: hcp_analytics.chart_province_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_province_title';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_province_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_province_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_province_title', 'Top Provinces by Healthcare Count') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_province_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_province_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_province_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Provinsi Teratas berdasarkan Jumlah Tenaga Kesehatan');
  END IF;

  -- key: hcp_analytics.chart_specialities_empty
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_specialities_empty';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_specialities_empty';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_specialities_empty' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_specialities_empty', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_specialities_empty', 'No speciality data available yet.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_specialities_empty_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_specialities_empty_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_specialities_empty_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Data spesialisasi belum tersedia.');
  END IF;

  -- key: hcp_analytics.chart_specialities_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'chart_specialities_title';
  IF v_key_id IS NULL THEN
    v_slug := 'chart_specialities_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'chart_specialities_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('chart_specialities_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'chart_specialities_title', 'Healthcare Specialities') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'chart_specialities_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'chart_specialities_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('chart_specialities_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Spesialisasi Kesehatan');
  END IF;

  -- key: hcp_analytics.col_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_education';
  IF v_key_id IS NULL THEN
    v_slug := 'col_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_education', 'EDUCATION') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PENDIDIKAN');
  END IF;

  -- key: hcp_analytics.col_license
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_license';
  IF v_key_id IS NULL THEN
    v_slug := 'col_license';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_license' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_license', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_license', 'LICENSE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_license_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_license_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_license_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'LISENSI');
  END IF;

  -- key: hcp_analytics.col_name
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_name';
  IF v_key_id IS NULL THEN
    v_slug := 'col_name';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_name' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_name', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_name', 'NAME') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_name_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_name_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_name_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NAMA');
  END IF;

  -- key: hcp_analytics.col_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_no';
  IF v_key_id IS NULL THEN
    v_slug := 'col_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_no', 'NO') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NO');
  END IF;

  -- key: hcp_analytics.col_place_of_practice
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_place_of_practice';
  IF v_key_id IS NULL THEN
    v_slug := 'col_place_of_practice';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_place_of_practice', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_place_of_practice', 'PLACE OF PRACTICE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_place_of_practice_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_place_of_practice_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TEMPAT PRAKTIK');
  END IF;

  -- key: hcp_analytics.col_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_province';
  IF v_key_id IS NULL THEN
    v_slug := 'col_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_province', 'PROVINCE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_province_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'PROVINCE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PROVINSI');
  END IF;

  -- key: hcp_analytics.col_specialities
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_specialities';
  IF v_key_id IS NULL THEN
    v_slug := 'col_specialities';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_specialities', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_specialities', 'SPECIALITIES') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_specialities_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_specialities_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'SPECIALITIES');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_specialities_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_specialities_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_specialities_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'SPESIALISASI');
  END IF;

  -- key: hcp_analytics.col_start_date
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_start_date';
  IF v_key_id IS NULL THEN
    v_slug := 'col_start_date';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_start_date', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_start_date', 'START DATE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_start_date_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'START DATE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_start_date_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TANGGAL MULAI');
  END IF;

  -- key: hcp_analytics.col_status
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_status';
  IF v_key_id IS NULL THEN
    v_slug := 'col_status';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_status' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_status', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_status', 'STATUS') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_status_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_status_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_status_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'STATUS');
  END IF;

  -- key: hcp_analytics.empty_state
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_state';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_state';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_state' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_state', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_state', 'No healthcare professionals found.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_state_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_state_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_state_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada tenaga kesehatan yang ditemukan.');
  END IF;

  -- key: hcp_analytics.filter_label_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_education';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_education', 'Education') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Pendidikan');
  END IF;

  -- key: hcp_analytics.filter_label_places
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_places';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_places';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_places' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_places', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_places', 'Hospital / Place') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_places_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_places_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_places_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Rumah Sakit / Tempat');
  END IF;

  -- key: hcp_analytics.filter_label_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_province';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_province', 'Province') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Provinsi');
  END IF;

  -- key: hcp_analytics.filter_label_specialities
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_specialities';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_specialities';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_specialities' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_specialities', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_specialities', 'Speciality') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_specialities_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_specialities_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_specialities_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Spesialisasi');
  END IF;

  -- key: hcp_analytics.label_entries
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_entries';
  IF v_key_id IS NULL THEN
    v_slug := 'label_entries';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_entries' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_entries', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_entries', 'entries') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'label_entries_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'entries');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_entries_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'entri');
  END IF;

  -- key: hcp_analytics.label_in_total
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_in_total';
  IF v_key_id IS NULL THEN
    v_slug := 'label_in_total';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_in_total', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_in_total', 'in total') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_in_total_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_in_total_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'total');
  END IF;

  -- key: hcp_analytics.label_of
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_of';
  IF v_key_id IS NULL THEN
    v_slug := 'label_of';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_of' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_of', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_of', 'of') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_of_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_of_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_of_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'dari');
  END IF;

  -- key: hcp_analytics.label_results
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_results';
  IF v_key_id IS NULL THEN
    v_slug := 'label_results';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_results' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_results', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_results', 'results') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_results_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_results_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_results_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'hasil');
  END IF;

  -- key: hcp_analytics.label_show
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_show';
  IF v_key_id IS NULL THEN
    v_slug := 'label_show';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_show' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_show', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_show', 'Show') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_show_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_show_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_show_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Menampilkan');
  END IF;

  -- key: hcp_analytics.label_to
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_to';
  IF v_key_id IS NULL THEN
    v_slug := 'label_to';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_to' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_to', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_to', 'to') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_to_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_to_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_to_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'sampai');
  END IF;

  -- key: hcp_analytics.page_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'page_title';
  IF v_key_id IS NULL THEN
    v_slug := 'page_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'page_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('page_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'page_title', 'Healthcare Professionals Analytics') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'page_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'page_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('page_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Analitik Tenaga Kesehatan');
  END IF;

  -- key: hcp_analytics.search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'search_placeholder', 'Search healthcare professionals in this table') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari tenaga kesehatan profesional di tabel ini');
  END IF;

  -- key: hcp_analytics.stat_across
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_across';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_across';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_across' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_across', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_across', 'Across') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_across_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_across_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_across_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Di');
  END IF;

  -- key: hcp_analytics.stat_active
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_active';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_active';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_active' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_active', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_active', 'Active Licenses') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_active_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_active_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_active_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Lisensi Aktif');
  END IF;

  -- key: hcp_analytics.stat_facilities
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_facilities';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_facilities';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_facilities' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_facilities', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_facilities', 'Practice Facilities') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_facilities_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_facilities_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_facilities_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Fasilitas Praktik');
  END IF;

  -- key: hcp_analytics.stat_inactive
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_inactive';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_inactive';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_inactive' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_inactive', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_inactive', 'Inactive') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_inactive_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_inactive_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_inactive_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak Aktif');
  END IF;

  -- key: hcp_analytics.stat_regions
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_regions';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_regions';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_regions' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_regions', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_regions', 'Regions') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_regions_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_regions_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_regions_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Wilayah');
  END IF;

  -- key: hcp_analytics.stat_total
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'stat_total';
  IF v_key_id IS NULL THEN
    v_slug := 'stat_total';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'stat_total' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('stat_total', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'stat_total', 'Total Health Care') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'stat_total_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'stat_total_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('stat_total_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Total Tenaga Kesehatan');
  END IF;

  -- key: hcp_analytics.status_active
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'status_active';
  IF v_key_id IS NULL THEN
    v_slug := 'status_active';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'status_active' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('status_active', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'status_active', 'Active') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'status_active_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'status_active_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('status_active_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Aktif');
  END IF;

  -- key: hcp_analytics.status_inactive
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'status_inactive';
  IF v_key_id IS NULL THEN
    v_slug := 'status_inactive';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'status_inactive' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('status_inactive', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'status_inactive', 'Inactive') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'status_inactive_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'status_inactive_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('status_inactive_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak Aktif');
  END IF;

  -- === Module: hospital_list ===
  SELECT id INTO v_module_id FROM base_translation_module WHERE code = 'hospital_list';
  IF v_module_id IS NULL THEN
    v_slug := 'hospital-list';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_module WHERE slug = v_slug) LOOP
      v_slug := 'hospital-list' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_module (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, code) VALUES ('Hospital - List', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, 'hospital_list') RETURNING id INTO v_module_id;
  END IF;

  -- key: hospital_list.page_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'page_title';
  IF v_key_id IS NULL THEN
    v_slug := 'page_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'page_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('page_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'page_title', 'Hospitals') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'page_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'page_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('page_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Rumah Sakit');
  END IF;

  -- key: hospital_list.search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'search_placeholder', 'Search Hospital') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari Rumah Sakit');
  END IF;

  -- key: hospital_list.btn_filter
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_filter';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_filter';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_filter', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_filter', 'Filter') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_filter_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_filter_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Filter');
  END IF;

  -- key: hospital_list.btn_export
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_export';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_export';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_export' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_export', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_export', 'Export') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_export_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_export_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_export_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Ekspor');
  END IF;

  -- key: hospital_list.col_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_no';
  IF v_key_id IS NULL THEN
    v_slug := 'col_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_no', 'NO') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NO');
  END IF;

  -- key: hospital_list.col_name
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_name';
  IF v_key_id IS NULL THEN
    v_slug := 'col_name';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_name' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_name', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_name', 'NAME') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_name_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_name_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_name_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NAMA');
  END IF;

  -- key: hospital_list.col_type
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_type';
  IF v_key_id IS NULL THEN
    v_slug := 'col_type';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_type' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_type', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_type', 'TYPE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_type_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_type_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_type_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'JENIS');
  END IF;

  -- key: hospital_list.col_class
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_class';
  IF v_key_id IS NULL THEN
    v_slug := 'col_class';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_class' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_class', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_class', 'CLASS') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_class_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_class_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_class_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'KELAS');
  END IF;

  -- key: hospital_list.col_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_province';
  IF v_key_id IS NULL THEN
    v_slug := 'col_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_province', 'PROVINCE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_province_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'PROVINCE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PROVINSI');
  END IF;

  -- key: hospital_list.col_regency
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_regency';
  IF v_key_id IS NULL THEN
    v_slug := 'col_regency';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_regency' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_regency', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_regency', 'REGENCY') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_regency_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_regency_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_regency_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'KABUPATEN/KOTA');
  END IF;

  -- key: hospital_list.empty_state
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_state';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_state';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_state' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_state', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_state', 'No hospitals found.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_state_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_state_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_state_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada rumah sakit yang ditemukan.');
  END IF;

  -- key: hospital_list.label_show
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_show';
  IF v_key_id IS NULL THEN
    v_slug := 'label_show';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_show' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_show', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_show', 'Show') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_show_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_show_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_show_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Menampilkan');
  END IF;

  -- key: hospital_list.label_entries
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_entries';
  IF v_key_id IS NULL THEN
    v_slug := 'label_entries';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_entries' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_entries', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_entries', 'entries') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'label_entries_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'entries');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_entries_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'entri');
  END IF;

  -- key: hospital_list.label_all
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_all';
  IF v_key_id IS NULL THEN
    v_slug := 'label_all';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_all' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_all', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_all', 'All') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_all_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_all_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_all_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Semua');
  END IF;

  -- key: hospital_list.label_in_total
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_in_total';
  IF v_key_id IS NULL THEN
    v_slug := 'label_in_total';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_in_total', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_in_total', 'in total') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_in_total_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_in_total_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_in_total_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'total');
  END IF;

  -- key: hospital_list.label_to
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_to';
  IF v_key_id IS NULL THEN
    v_slug := 'label_to';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_to' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_to', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_to', 'to') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_to_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_to_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_to_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'sampai');
  END IF;

  -- key: hospital_list.label_of
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_of';
  IF v_key_id IS NULL THEN
    v_slug := 'label_of';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_of' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_of', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_of', 'of') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_of_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_of_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_of_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'dari');
  END IF;

  -- key: hospital_list.label_results
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_results';
  IF v_key_id IS NULL THEN
    v_slug := 'label_results';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_results' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_results', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_results', 'results') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_results_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_results_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_results_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'hasil');
  END IF;

  -- === Module: hcp_profile ===
  SELECT id INTO v_module_id FROM base_translation_module WHERE code = 'hcp_profile';
  IF v_module_id IS NULL THEN
    v_slug := 'healthcare-professionals-profile';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_module WHERE slug = v_slug) LOOP
      v_slug := 'healthcare-professionals-profile' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_module (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, code) VALUES ('Healthcare Professionals - Profile', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, 'hcp_profile') RETURNING id INTO v_module_id;
  END IF;

  -- key: hcp_profile.page_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'page_title';
  IF v_key_id IS NULL THEN
    v_slug := 'page_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'page_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('page_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'page_title', 'Healthcare Professionals') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'page_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'page_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('page_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tenaga Kesehatan');
  END IF;

  -- key: hcp_profile.btn_back
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_back';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_back';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_back' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_back', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_back', 'Back') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_back_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_back_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_back_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kembali');
  END IF;

  -- key: hcp_profile.search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'search_placeholder', 'Search') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari');
  END IF;

  -- key: hcp_profile.profile_link_label
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'profile_link_label';
  IF v_key_id IS NULL THEN
    v_slug := 'profile_link_label';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'profile_link_label' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('profile_link_label', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'profile_link_label', 'Profile link') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'profile_link_label_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'profile_link_label_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('profile_link_label_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tautan profil');
  END IF;

  -- key: hcp_profile.about_prefix
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'about_prefix';
  IF v_key_id IS NULL THEN
    v_slug := 'about_prefix';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'about_prefix' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('about_prefix', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'about_prefix', 'About') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'about_prefix_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'about_prefix_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('about_prefix_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tentang');
  END IF;

  -- key: hcp_profile.label_experience
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_experience';
  IF v_key_id IS NULL THEN
    v_slug := 'label_experience';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_experience' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_experience', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_experience', 'Experience') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_experience_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_experience_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_experience_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Pengalaman');
  END IF;

  -- key: hcp_profile.label_license_str
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_license_str';
  IF v_key_id IS NULL THEN
    v_slug := 'label_license_str';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_license_str' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_license_str', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_license_str', 'License (STR)') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_license_str_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_license_str_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_license_str_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Lisensi (STR)');
  END IF;

  -- key: hcp_profile.section_place_of_practice
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_place_of_practice';
  IF v_key_id IS NULL THEN
    v_slug := 'section_place_of_practice';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_place_of_practice' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_place_of_practice', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_place_of_practice', 'Place of Practice') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_place_of_practice_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_place_of_practice_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_place_of_practice_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tempat Praktik');
  END IF;

  -- key: hcp_profile.col_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_no';
  IF v_key_id IS NULL THEN
    v_slug := 'col_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_no', 'NO') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NO');
  END IF;

  -- key: hcp_profile.col_place_of_practice
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_place_of_practice';
  IF v_key_id IS NULL THEN
    v_slug := 'col_place_of_practice';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_place_of_practice', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_place_of_practice', 'PLACE OF PRACTICE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_place_of_practice_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_place_of_practice_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_place_of_practice_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TEMPAT PRAKTIK');
  END IF;

  -- key: hcp_profile.col_city
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_city';
  IF v_key_id IS NULL THEN
    v_slug := 'col_city';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_city' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_city', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_city', 'CITY') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_city_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_city_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_city_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'KOTA');
  END IF;

  -- key: hcp_profile.col_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_province';
  IF v_key_id IS NULL THEN
    v_slug := 'col_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_province', 'PROVINCE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_province_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'PROVINCE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PROVINSI');
  END IF;

  -- key: hcp_profile.empty_place_of_practice
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_place_of_practice';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_place_of_practice';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_place_of_practice' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_place_of_practice', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_place_of_practice', 'No place of practice on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_place_of_practice_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_place_of_practice_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_place_of_practice_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada tempat praktik yang tercatat.');
  END IF;

  -- key: hcp_profile.section_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_education';
  IF v_key_id IS NULL THEN
    v_slug := 'section_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_education', 'Education') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Pendidikan');
  END IF;

  -- key: hcp_profile.col_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_education';
  IF v_key_id IS NULL THEN
    v_slug := 'col_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_education', 'EDUCATION') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PENDIDIKAN');
  END IF;

  -- key: hcp_profile.col_completed_date
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_completed_date';
  IF v_key_id IS NULL THEN
    v_slug := 'col_completed_date';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_completed_date' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_completed_date', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_completed_date', 'COMPLETED DATE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_completed_date_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_completed_date_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_completed_date_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TANGGAL SELESAI');
  END IF;

  -- key: hcp_profile.empty_education
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_education';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_education';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_education' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_education', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_education', 'No education on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_education_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_education_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_education_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada riwayat pendidikan yang tercatat.');
  END IF;

  -- key: hcp_profile.section_speciality
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_speciality';
  IF v_key_id IS NULL THEN
    v_slug := 'section_speciality';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_speciality' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_speciality', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_speciality', 'Speciality') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_speciality_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_speciality_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_speciality_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Spesialisasi');
  END IF;

  -- key: hcp_profile.col_speciality
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_speciality';
  IF v_key_id IS NULL THEN
    v_slug := 'col_speciality';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_speciality' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_speciality', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_speciality', 'SPECIALITY') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_speciality_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_speciality_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_speciality_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'SPESIALISASI');
  END IF;

  -- key: hcp_profile.empty_speciality
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_speciality';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_speciality';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_speciality' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_speciality', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_speciality', 'No speciality on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_speciality_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_speciality_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_speciality_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada spesialisasi yang tercatat.');
  END IF;

  -- === Module: hospital_profile ===
  SELECT id INTO v_module_id FROM base_translation_module WHERE code = 'hospital_profile';
  IF v_module_id IS NULL THEN
    v_slug := 'hospital-profile';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_module WHERE slug = v_slug) LOOP
      v_slug := 'hospital-profile' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_module (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, code) VALUES ('Hospital - Profile', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, 'hospital_profile') RETURNING id INTO v_module_id;
  END IF;

  -- key: hospital_profile.page_title
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'page_title';
  IF v_key_id IS NULL THEN
    v_slug := 'page_title';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'page_title' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('page_title', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'page_title', 'Hospitals') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'page_title_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'page_title_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('page_title_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Rumah Sakit');
  END IF;

  -- key: hospital_profile.btn_back
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_back';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_back';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_back' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_back', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_back', 'Back') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_back_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_back_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_back_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kembali');
  END IF;

  -- key: hospital_profile.search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'search_placeholder', 'Search Hospital') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari Rumah Sakit');
  END IF;

  -- key: hospital_profile.label_director
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_director';
  IF v_key_id IS NULL THEN
    v_slug := 'label_director';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_director' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_director', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_director', 'Director') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_director_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_director_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_director_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Direktur');
  END IF;

  -- key: hospital_profile.label_phone
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_phone';
  IF v_key_id IS NULL THEN
    v_slug := 'label_phone';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_phone' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_phone', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_phone', 'Phone') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_phone_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_phone_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_phone_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Telepon');
  END IF;

  -- key: hospital_profile.about_prefix
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'about_prefix';
  IF v_key_id IS NULL THEN
    v_slug := 'about_prefix';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'about_prefix' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('about_prefix', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'about_prefix', 'About') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'about_prefix_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'about_prefix_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('about_prefix_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tentang');
  END IF;

  -- key: hospital_profile.label_is_customer
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_is_customer';
  IF v_key_id IS NULL THEN
    v_slug := 'label_is_customer';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_is_customer' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_is_customer', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_is_customer', 'Is Customer?') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_is_customer_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_is_customer_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_is_customer_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Apakah Pelanggan?');
  END IF;

  -- key: hospital_profile.label_yes
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_yes';
  IF v_key_id IS NULL THEN
    v_slug := 'label_yes';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_yes' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_yes', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_yes', 'Yes') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_yes_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_yes_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_yes_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Ya');
  END IF;

  -- key: hospital_profile.label_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_no';
  IF v_key_id IS NULL THEN
    v_slug := 'label_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_no', 'No') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak');
  END IF;

  -- key: hospital_profile.label_ownership
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_ownership';
  IF v_key_id IS NULL THEN
    v_slug := 'label_ownership';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_ownership' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_ownership', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_ownership', 'Ownership') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_ownership_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_ownership_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_ownership_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kepemilikan');
  END IF;

  -- key: hospital_profile.label_blu_status
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_blu_status';
  IF v_key_id IS NULL THEN
    v_slug := 'label_blu_status';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_blu_status' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_blu_status', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_blu_status', 'BLU Status') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_blu_status_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_blu_status_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_blu_status_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Status BLU');
  END IF;

  -- key: hospital_profile.label_province
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_province';
  IF v_key_id IS NULL THEN
    v_slug := 'label_province';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_province' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_province', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_province', 'Province') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_province_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_province_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_province_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Provinsi');
  END IF;

  -- key: hospital_profile.label_regency
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_regency';
  IF v_key_id IS NULL THEN
    v_slug := 'label_regency';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_regency' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_regency', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_regency', 'Regency') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_regency_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_regency_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_regency_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kabupaten/Kota');
  END IF;

  -- key: hospital_profile.label_district
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_district';
  IF v_key_id IS NULL THEN
    v_slug := 'label_district';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_district' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_district', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_district', 'District') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_district_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_district_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_district_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kecamatan');
  END IF;

  -- key: hospital_profile.label_village
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_village';
  IF v_key_id IS NULL THEN
    v_slug := 'label_village';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_village' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_village', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_village', 'Village') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_village_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_village_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_village_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kelurahan/Desa');
  END IF;

  -- key: hospital_profile.label_building
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_building';
  IF v_key_id IS NULL THEN
    v_slug := 'label_building';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_building' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_building', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_building', 'Building') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_building_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_building_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_building_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Gedung');
  END IF;

  -- key: hospital_profile.label_complex
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_complex';
  IF v_key_id IS NULL THEN
    v_slug := 'label_complex';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_complex' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_complex', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_complex', 'Complex') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_complex_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_complex_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_complex_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kompleks');
  END IF;

  -- key: hospital_profile.section_hospital_location
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_hospital_location';
  IF v_key_id IS NULL THEN
    v_slug := 'section_hospital_location';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_hospital_location' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_hospital_location', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_hospital_location', 'Hospital Location') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_hospital_location_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_hospital_location_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_hospital_location_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Lokasi Rumah Sakit');
  END IF;

  -- key: hospital_profile.section_doctors
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_doctors';
  IF v_key_id IS NULL THEN
    v_slug := 'section_doctors';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_doctors' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_doctors', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_doctors', 'Doctors') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_doctors_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_doctors_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_doctors_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Dokter');
  END IF;

  -- key: hospital_profile.section_bed_count
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_bed_count';
  IF v_key_id IS NULL THEN
    v_slug := 'section_bed_count';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_bed_count' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_bed_count', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_bed_count', 'Bed Count') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_bed_count_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_bed_count_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_bed_count_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Jumlah Tempat Tidur');
  END IF;

  -- key: hospital_profile.section_services
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_services';
  IF v_key_id IS NULL THEN
    v_slug := 'section_services';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_services' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_services', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_services', 'Services') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_services_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_services_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_services_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Layanan');
  END IF;

  -- key: hospital_profile.section_professional_group
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'section_professional_group';
  IF v_key_id IS NULL THEN
    v_slug := 'section_professional_group';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'section_professional_group' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('section_professional_group', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'section_professional_group', 'Professional Group') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'section_professional_group_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'section_professional_group_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('section_professional_group_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kelompok Profesi');
  END IF;

  -- key: hospital_profile.col_no
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_no';
  IF v_key_id IS NULL THEN
    v_slug := 'col_no';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_no' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_no', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_no', 'NO') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_no_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_no_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_no_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NO');
  END IF;

  -- key: hospital_profile.col_name
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_name';
  IF v_key_id IS NULL THEN
    v_slug := 'col_name';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_name' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_name', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_name', 'NAME') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_name_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_name_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_name_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'NAMA');
  END IF;

  -- key: hospital_profile.col_license
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_license';
  IF v_key_id IS NULL THEN
    v_slug := 'col_license';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_license' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_license', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_license', 'LICENSE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_license_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_license_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_license_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'LISENSI');
  END IF;

  -- key: hospital_profile.col_specialties
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_specialties';
  IF v_key_id IS NULL THEN
    v_slug := 'col_specialties';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_specialties' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_specialties', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_specialties', 'SPECIALTIES') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_specialties_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_specialties_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_specialties_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'SPESIALISASI');
  END IF;

  -- key: hospital_profile.col_start_date
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_start_date';
  IF v_key_id IS NULL THEN
    v_slug := 'col_start_date';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_start_date', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_start_date', 'START DATE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'col_start_date_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'START DATE');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_start_date_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_start_date_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_start_date_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'TANGGAL MULAI');
  END IF;

  -- key: hospital_profile.col_class
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_class';
  IF v_key_id IS NULL THEN
    v_slug := 'col_class';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_class' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_class', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_class', 'CLASS') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_class_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_class_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_class_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'KELAS');
  END IF;

  -- key: hospital_profile.col_count
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_count';
  IF v_key_id IS NULL THEN
    v_slug := 'col_count';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_count' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_count', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_count', 'COUNT') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_count_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_count_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_count_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'JUMLAH');
  END IF;

  -- key: hospital_profile.col_service
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_service';
  IF v_key_id IS NULL THEN
    v_slug := 'col_service';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_service' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_service', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_service', 'SERVICE') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_service_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_service_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_service_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'LAYANAN');
  END IF;

  -- key: hospital_profile.col_professional
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'col_professional';
  IF v_key_id IS NULL THEN
    v_slug := 'col_professional';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'col_professional' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('col_professional', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'col_professional', 'PROFESSIONAL') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'col_professional_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'col_professional_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('col_professional_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'PROFESI');
  END IF;

  -- key: hospital_profile.empty_doctors
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_doctors';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_doctors';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_doctors' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_doctors', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_doctors', 'No doctors linked to this hospital.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_doctors_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_doctors_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_doctors_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada dokter yang terhubung dengan rumah sakit ini.');
  END IF;

  -- key: hospital_profile.empty_beds
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_beds';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_beds';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_beds' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_beds', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_beds', 'No bed data on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_beds_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_beds_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_beds_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada data tempat tidur yang tercatat.');
  END IF;

  -- key: hospital_profile.empty_services
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_services';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_services';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_services' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_services', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_services', 'No service data on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_services_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_services_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_services_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada data layanan yang tercatat.');
  END IF;

  -- key: hospital_profile.empty_professionals
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_professionals';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_professionals';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_professionals' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_professionals', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_professionals', 'No professional group data on file.') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_professionals_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_professionals_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_professionals_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada data kelompok profesi yang tercatat.');
  END IF;

  -- key: hospital_profile.filter_label_specialties
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_specialties';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_specialties';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_specialties' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_specialties', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_specialties', 'Specialties') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_specialties_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_specialties_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_specialties_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Spesialisasi');
  END IF;

  -- key: hospital_profile.filter_label_class
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_class';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_class';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_class' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_class', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_class', 'Class') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_class_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_class_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_class_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Kelas');
  END IF;

  -- key: hospital_profile.filter_label_service
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_service';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_service';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_service' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_service', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_service', 'Service') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_service_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_service_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_service_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Layanan');
  END IF;

  -- key: hospital_profile.filter_label_professional
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_label_professional';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_label_professional';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_professional' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_label_professional', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_label_professional', 'Professional') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_label_professional_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_label_professional_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_label_professional_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Profesi');
  END IF;

  -- key: hospital_profile.btn_filter
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_filter';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_filter';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_filter', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_filter', 'Filter') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_filter_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_filter_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_filter_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Filter');
  END IF;

  -- key: hospital_profile.btn_reset
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_reset';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_reset';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_reset' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_reset', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_reset', 'Reset') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_reset_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_reset_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_reset_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Atur Ulang');
  END IF;

  -- key: hospital_profile.btn_confirm
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'btn_confirm';
  IF v_key_id IS NULL THEN
    v_slug := 'btn_confirm';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'btn_confirm' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('btn_confirm', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'btn_confirm', 'Confirm') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'btn_confirm_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'btn_confirm_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('btn_confirm_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Konfirmasi');
  END IF;

  -- key: hospital_profile.filter_search_placeholder
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'filter_search_placeholder';
  IF v_key_id IS NULL THEN
    v_slug := 'filter_search_placeholder';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'filter_search_placeholder' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('filter_search_placeholder', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'filter_search_placeholder', 'Search') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'filter_search_placeholder_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'filter_search_placeholder_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('filter_search_placeholder_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Cari');
  END IF;

  -- key: hospital_profile.label_show
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_show';
  IF v_key_id IS NULL THEN
    v_slug := 'label_show';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_show' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_show', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_show', 'Show') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_show_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_show_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_show_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Menampilkan');
  END IF;

  -- key: hospital_profile.label_entries
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_entries';
  IF v_key_id IS NULL THEN
    v_slug := 'label_entries';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_entries' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_entries', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_entries', 'entries') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'en') THEN
    v_slug := 'label_entries_en';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_en' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_en', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'en', 'entries');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_entries_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_entries_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_entries_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'entri');
  END IF;

  -- key: hospital_profile.label_all
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_all';
  IF v_key_id IS NULL THEN
    v_slug := 'label_all';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_all' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_all', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_all', 'All') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_all_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_all_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_all_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Semua');
  END IF;

  -- key: hospital_profile.label_showing
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_showing';
  IF v_key_id IS NULL THEN
    v_slug := 'label_showing';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_showing' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_showing', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_showing', 'Showing') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_showing_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_showing_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_showing_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Menampilkan');
  END IF;

  -- key: hospital_profile.label_to
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_to';
  IF v_key_id IS NULL THEN
    v_slug := 'label_to';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_to' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_to', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_to', 'to') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_to_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_to_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_to_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'sampai');
  END IF;

  -- key: hospital_profile.label_of
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'label_of';
  IF v_key_id IS NULL THEN
    v_slug := 'label_of';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'label_of' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('label_of', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'label_of', 'of') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'label_of_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'label_of_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('label_of_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'dari');
  END IF;

  -- key: hospital_profile.empty_no_matching
  SELECT id INTO v_key_id FROM base_translation_key WHERE module_id = v_module_id AND key = 'empty_no_matching';
  IF v_key_id IS NULL THEN
    v_slug := 'empty_no_matching';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation_key WHERE slug = v_slug) LOOP
      v_slug := 'empty_no_matching' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation_key (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, module_id, key, default_value) VALUES ('empty_no_matching', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_module_id, 'empty_no_matching', 'No matching entries found') RETURNING id INTO v_key_id;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM base_translation WHERE translation_key_id = v_key_id AND language = 'id') THEN
    v_slug := 'empty_no_matching_id';
    v_counter := 1;
    WHILE EXISTS (SELECT 1 FROM base_translation WHERE slug = v_slug) LOOP
      v_slug := 'empty_no_matching_id' || '-' || v_counter;
      v_counter := v_counter + 1;
    END LOOP;
    INSERT INTO base_translation (name, description, remark, status, slug, cat, cby_id, uat, uby_id, dat, dby_id, deleted, translation_key_id, language, value) VALUES ('empty_no_matching_id', '', NULL, 1, v_slug, now(), NULL, NULL, NULL, NULL, NULL, false, v_key_id, 'id', 'Tidak ada entri yang cocok ditemukan');
  END IF;

END $$;
"""


class Command(BaseCommand):
    help = "Seed hospital_list / hcp_profile / hospital_profile translations (idempotent)."

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute(TRANSLATION_SEED_SQL)
            self.stdout.write(self.style.SUCCESS("Translation seed applied (or already up to date)."))
        except Exception as e:
            logger.exception("Translation seed failed")
            self.stdout.write(self.style.ERROR(f"Translation seed failed: {e}"))
