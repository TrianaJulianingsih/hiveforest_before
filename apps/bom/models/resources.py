from import_export import fields, resources

from apps.bom.models.freight import FreightCostDetail


class FreightCostDetailReportResource(resources.ModelResource):
    freight_number = fields.Field(column_name="FREIGHT NUMBER")
    shipping_date = fields.Field(column_name="SHIPPING_DATE")
    from_location = fields.Field(column_name="FROM_LOCATION")
    to_location = fields.Field(column_name="TO_LOCATION")
    expedition_name = fields.Field(column_name="EXPEDITION_NAME")
    expedition_type = fields.Field(column_name="EXPEDITION_TYPE")
    packaging_type = fields.Field(column_name="PACKAGING_TYPE")
    item_code = fields.Field(column_name="ITEM_CODE")
    item_description = fields.Field(column_name="ITEM_DESCRIPTION")
    qty_freight = fields.Field(column_name="QTY_FREIGHT", attribute="qty_freight")
    total_weight = fields.Field(column_name="TOTAL_WEIGHT", attribute="total_weight")
    nama_principal = fields.Field(column_name="NAMA_PRINCIPAL")
    group_produk = fields.Field(column_name="GROUP_PRODUK")
    total_freight = fields.Field(column_name="TOTAL_FREIGHT", attribute="total_freight")
    freight_type = fields.Field(column_name="FREIGHT_TYPE")
    total_cost = fields.Field(column_name="TOTAL_COST", attribute="total_cost")
    kode_cab = fields.Field(column_name="kode_cab")
    nama_cab = fields.Field(column_name="nama_cab")
    item_group = fields.Field(column_name="ItemGroup", attribute="item_group")

    class Meta:
        model = FreightCostDetail
        fields = (
            "freight_number",
            "shipping_date",
            "from_location",
            "to_location",
            "expedition_name",
            "expedition_type",
            "packaging_type",
            "item_code",
            "item_description",
            "qty_freight",
            "total_weight",
            "nama_principal",
            "group_produk",
            "total_freight",
            "freight_type",
            "total_cost",
            "kode_cab",
            "nama_cab",
            "item_group",
        )
        export_order = (
            "freight_number",
            "shipping_date",
            "from_location",
            "to_location",
            "expedition_name",
            "expedition_type",
            "packaging_type",
            "item_code",
            "item_description",
            "qty_freight",
            "total_weight",
            "nama_principal",
            "group_produk",
            "total_freight",
            "freight_type",
            "total_cost",
            "kode_cab",
            "nama_cab",
            "item_group",
        )

    def dehydrate_freight_number(self, obj):
        return obj.freight.name if obj.freight else ""

    def dehydrate_shipping_date(self, obj):
        return obj.freight.shipping_date if obj.freight else None

    def dehydrate_from_location(self, obj):
        return obj.from_location

    def dehydrate_to_location(self, obj):
        return obj.to_location

    def dehydrate_expedition_name(self, obj):
        return obj.expedition_name

    def dehydrate_expedition_type(self, obj):
        return obj.expedition_type

    def dehydrate_packaging_type(self, obj):
        return obj.packaging_type_value

    def dehydrate_item_code(self, obj):
        return obj.item_code

    def dehydrate_item_description(self, obj):
        return obj.item_description

    def dehydrate_nama_principal(self, obj):
        return obj.nama_principal

    def dehydrate_group_produk(self, obj):
        return obj.group_produk

    def dehydrate_freight_type(self, obj):
        return obj.freight.freight_type if obj.freight else ""

    def dehydrate_kode_cab(self, obj):
        return obj.kode_cab

    def dehydrate_nama_cab(self, obj):
        return obj.nama_cab

    def dehydrate_item_group(self, obj):
        return obj.item_group_name
