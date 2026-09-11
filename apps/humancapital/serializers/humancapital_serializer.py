from rest_framework import serializers
from apps.humancapital.models.structure import Organization

# ╔════════════════════════════════════════════════════════════════╗
# ║  Name: OrganizationTree                                        ║
# ║  Type: Class Base View                                         ║
# ║  Purpose: Serialize organization                               ║
# ╟────────────────────────────────────────────────────────────────╢
# ║  Path: apps\humancapital\serializers\humancapital_serializer.py║
# ║  Created: Jun/4-2025 by Setiadji                               ║
# ║  Updated:                                                      ║
# ╚════════════════════════════════════════════════════════════════╝
class OrganizationTree(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'children']

    def get_children(self, obj):
        children = Organization.objects.filter(parent=obj, deleted=False)
        return OrganizationTree(children, many=True).data