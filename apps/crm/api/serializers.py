from rest_framework import serializers

from apps.crm.models import Doctor


def name_or(related, fallback=None):
    # Mirrors hiveforest-api's app/modules/health_care_professional/utils.py name_or()
    if related:
        return related.name
    return fallback or None


def joined(values):
    # Mirrors hiveforest-api's app/modules/health_care_professional/utils.py joined()
    seen = [v for v in dict.fromkeys(values) if v]
    return ", ".join(seen) if seen else "-"


class DoctorListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField()
    license = serializers.SerializerMethodField()
    specialities = serializers.SerializerMethodField()
    start_period = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()
    status = serializers.IntegerField()

    def get_license(self, obj):
        return obj.license or None

    def get_specialities(self, obj):
        return obj.specialities_display

    def get_start_period(self, obj):
        return obj.start_period

    def get_province(self, obj):
        return joined(name_or(place.province, place.province_desc) for place in obj.doctorplace_set.all())

    def get_education(self, obj):
        return joined(education.institution for education in obj.doctoreducation_set.all())

    def get_place(self, obj):
        return joined(place.place_desc for place in obj.doctorplace_set.all())


class DoctorPlaceSerializer(serializers.Serializer):
    place = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()

    def get_place(self, obj):
        return obj.place_desc or "-"

    def get_city(self, obj):
        return name_or(obj.city, obj.city_desc)

    def get_province(self, obj):
        return name_or(obj.province, obj.province_desc)


class DoctorEducationSerializer(serializers.Serializer):
    institution = serializers.SerializerMethodField()
    completed_period = serializers.SerializerMethodField()

    def get_institution(self, obj):
        return obj.institution or "-"

    def get_completed_period(self, obj):
        return obj.completed_period


class DoctorDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    specialities = serializers.SerializerMethodField()
    license = serializers.SerializerMethodField()
    start_period = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    places = serializers.SerializerMethodField()
    educations = serializers.SerializerMethodField()

    def get_specialities(self, obj):
        return obj.specialities_display

    def get_license(self, obj):
        return obj.license or None

    def get_start_period(self, obj):
        return obj.start_period

    def get_experience(self, obj):
        return obj.experience_display

    def get_places(self, obj):
        return DoctorPlaceSerializer(obj.doctorplace_set.all(), many=True).data

    def get_educations(self, obj):
        return DoctorEducationSerializer(obj.doctoreducation_set.all(), many=True).data


class DoctorWriteSerializer(serializers.Serializer):
    # Mirrors hiveforest-api's DoctorCreateItem/DoctorUpdateRequest field set and length
    # constraints exactly.
    name = serializers.CharField(required=False, allow_blank=False, min_length=1, max_length=100)
    license = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    start_year = serializers.IntegerField(required=False, allow_null=True, min_value=1900, max_value=2100)
    start_month = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
    private_practice = serializers.BooleanField(required=False, allow_null=True)
    status = serializers.IntegerField(required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    remark = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)


class DoctorCreateSerializer(DoctorWriteSerializer):
    name = serializers.CharField(required=True, allow_blank=False, min_length=1, max_length=100)


class TopItemSerializer(serializers.Serializer):
    label = serializers.CharField()
    count = serializers.IntegerField()


class HospitalWriteSerializer(serializers.Serializer):
    # Mirrors hiveforest-api's HospitalCreateItem/HospitalUpdateRequest field set and
    # length constraints exactly (hiveforest-api validates first via Pydantic; this is
    # defense-in-depth plus the source of truth for anyone calling this API directly).
    name = serializers.CharField(required=False, allow_blank=False, min_length=1, max_length=100)
    code = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    raw_type = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=50)
    raw_class = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=25)
    raw_province = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    raw_city = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    raw_address = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    raw_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=50)
    raw_director = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    raw_ownership = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    raw_blustat = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=25)
    building = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    complex = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    status = serializers.IntegerField(required=False)


class HospitalCreateSerializer(HospitalWriteSerializer):
    name = serializers.CharField(required=True, allow_blank=False, min_length=1, max_length=100)


class HospitalListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField(allow_null=True, allow_blank=True)
    name = serializers.CharField()
    type = serializers.SerializerMethodField()
    hospital_class = serializers.SerializerMethodField()
    regency = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    status = serializers.IntegerField()

    def get_type(self, obj):
        return name_or(obj.hospitaltype)

    def get_hospital_class(self, obj):
        return name_or(obj.hospitalclass)

    def get_regency(self, obj):
        return name_or(obj.regency)

    def get_province(self, obj):
        return name_or(obj.province)


class ProfessionalGroupSerializer(serializers.Serializer):
    group = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_group(self, obj):
        return obj.raw_profgroup or "-"

    def get_count(self, obj):
        return obj.raw_profs or 0


class HospitalBedSerializer(serializers.Serializer):
    hospital_class = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_hospital_class(self, obj):
        return obj.raw_bedclass or "-"

    def get_count(self, obj):
        return obj.raw_beds or 0


class HospitalServiceSerializer(serializers.Serializer):
    service = serializers.SerializerMethodField()

    def get_service(self, obj):
        return obj.raw_service or "-"


class HospitalDoctorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    license = serializers.SerializerMethodField()
    specialities = serializers.SerializerMethodField()
    start_period = serializers.SerializerMethodField()

    def get_license(self, obj):
        return obj.license or None

    def get_specialities(self, obj):
        return obj.specialities_display

    def get_start_period(self, obj):
        return obj.start_period


class HospitalDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    director = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    is_customer = serializers.SerializerMethodField()
    ownership = serializers.SerializerMethodField()
    blu_status = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()
    regency = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    village = serializers.SerializerMethodField()
    building = serializers.SerializerMethodField()
    complex = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    map_query = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    professional_groups = serializers.SerializerMethodField()
    doctors = serializers.SerializerMethodField()
    beds = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()

    def get_director(self, obj):
        return obj.raw_director or None

    def get_phone(self, obj):
        return obj.raw_phone or None

    def get_is_customer(self, obj):
        return bool(obj.customer_id)

    def get_ownership(self, obj):
        return name_or(obj.ownership, obj.raw_ownership)

    def get_blu_status(self, obj):
        return obj.raw_blustat or None

    def get_province(self, obj):
        return name_or(obj.province, obj.raw_province)

    def get_regency(self, obj):
        return name_or(obj.regency, obj.raw_city)

    def get_district(self, obj):
        return name_or(obj.district)

    def get_village(self, obj):
        return name_or(obj.village)

    def get_building(self, obj):
        return obj.building or None

    def get_complex(self, obj):
        return obj.complex or None

    def get_address(self, obj):
        return obj.raw_address or obj.map_search_query or None

    def get_map_query(self, obj):
        return obj.map_search_query or None

    def get_latitude(self, obj):
        return float(obj.latitude) if obj.latitude is not None else None

    def get_longitude(self, obj):
        return float(obj.longitude) if obj.longitude is not None else None

    def get_professional_groups(self, obj):
        return ProfessionalGroupSerializer(obj.hospitalprofessional_set.all(), many=True).data

    def get_beds(self, obj):
        return HospitalBedSerializer(obj.hospitalbed_set.all(), many=True).data

    def get_services(self, obj):
        return HospitalServiceSerializer(obj.hospitalservice_set.all(), many=True).data

    def get_doctors(self, obj):
        if not obj.customer_id:
            return []
        doctors = (
            Doctor.nondeleted_objects.filter(doctorplace__customer_id=obj.customer_id)
            .prefetch_related("doctorspeciality_set")
            .distinct()
            .order_by("name")
        )
        return HospitalDoctorSerializer(doctors, many=True).data
