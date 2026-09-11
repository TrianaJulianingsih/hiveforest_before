import django.db.models.deletion
from django.db import migrations, models


def ensure_business_rows(apps, schema_editor):
    Business = apps.get_model("humancapital", "Business")
    Organization = apps.get_model("humancapital", "Organization")

    business_sources = [
        (1, 2, "B-1000", "CIBG Business Unit"),
        (2, 3, "B-2000", "TMBG"),
    ]

    for business_id, organization_id, fallback_code, fallback_name in business_sources:
        organization = Organization.objects.filter(pk=organization_id).first()
        defaults = {
            "code": fallback_code,
            "name": fallback_name,
            "status": 1,
            "deleted": False,
        }

        if organization is not None:
            defaults.update(
                {
                    "code": (organization.code or fallback_code).replace("O-", "B-", 1),
                    "name": organization.name or fallback_name,
                    "description": organization.description,
                    "remark": organization.remark,
                    "status": organization.status,
                    "initial": organization.initial,
                    "shortname": getattr(organization, "shortname", None),
                    "effective": organization.effective,
                    "terminated": organization.terminated,
                    "deleted": organization.deleted,
                }
            )

        Business.objects.update_or_create(id=business_id, defaults=defaults)

    schema_editor.execute(
        "SELECT setval(pg_get_serial_sequence('humancapital_business', 'id'), "
        "COALESCE((SELECT MAX(id) FROM humancapital_business), 1), true)"
    )


def remap_business_ids(apps, schema_editor):
    Product = apps.get_model("sales", "Product")
    ProductSubgroup = apps.get_model("sales", "ProductSubgroup")
    ProductGroup = apps.get_model("sales", "ProductGroup")
    ECatalog = apps.get_model("sales", "ECatalog")

    models_to_update = [Product, ProductSubgroup, ProductGroup, ECatalog]

    for model in models_to_update:
        model.objects.exclude(business_id__in=[2, 3]).update(business_id=None)
        model.objects.filter(business_id=2).update(business_id=1)
        model.objects.filter(business_id=3).update(business_id=2)


class Migration(migrations.Migration):

    dependencies = [
        ("humancapital", "0035_business"),
        ("sales", "0093_salesregion_position_and_business"),
    ]

    operations = [
        migrations.RunPython(
            ensure_business_rows,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(remap_business_ids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
        migrations.AlterField(
            model_name="productsubgroup",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
        migrations.AlterField(
            model_name="productgroup",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
        migrations.AlterField(
            model_name="ecatalog",
            name="business",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="humancapital.business",
                verbose_name="Business",
            ),
        ),
    ]