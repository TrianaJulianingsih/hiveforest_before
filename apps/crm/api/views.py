import calendar
import json
import uuid

from django.db.models import Count, Prefetch, Q
from django.db.models.functions import Coalesce
from django.http import StreamingHttpResponse
from django_currentuser.middleware import SetCurrentUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.models import Person
from apps.crm.models import Doctor, DoctorEducation, DoctorPlace, DoctorSpeciality, Hospital

from .authentication import InternalServiceAuthentication
from .pagination import paginate
from .permissions import IsStaffOrSuperuser
from .serializers import (
    DoctorCreateSerializer,
    DoctorDetailSerializer,
    DoctorListSerializer,
    DoctorWriteSerializer,
    HospitalCreateSerializer,
    HospitalDetailSerializer,
    HospitalListSerializer,
    HospitalWriteSerializer,
    TopItemSerializer,
)


def _filtered_hospitals(request):
    q = request.query_params.get("q")
    type_ = request.query_params.getlist("type") or None
    hospital_class = request.query_params.getlist("class") or None
    regency = request.query_params.getlist("regency") or None
    province = request.query_params.getlist("province") or None

    hospitals = Hospital.nondeleted_objects.select_related(
        "hospitaltype", "hospitalclass", "province", "regency"
    ).order_by("name")

    if q:
        hospitals = hospitals.filter(name__icontains=q)
    if type_:
        hospitals = hospitals.filter(hospitaltype__name__in=type_)
    if hospital_class:
        hospitals = hospitals.filter(hospitalclass__name__in=hospital_class)
    if regency:
        hospitals = hospitals.filter(regency__name__in=regency)
    if province:
        hospitals = hospitals.filter(province__name__in=province)
    if type_ or hospital_class or regency or province:
        hospitals = hospitals.distinct()

    return hospitals


def _unique_code(requested):
    # Mirrors hiveforest-api's HospitalRepository._unique_code(): Hospital.save() below
    # unconditionally appends to `code` on every save, so every write here must reset it
    # to a short fresh value first or the varchar(100) column overflows on repeated saves
    # (confirmed via a real production crash during hiveforest-api's original ORM-based
    # implementation this workaround was ported from).
    code = (requested or "").strip()
    return code or f"API-{uuid.uuid4().hex[:12]}"


class HospitalListView(APIView):
    authentication_classes = [InternalServiceAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsStaffOrSuperuser()]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        items, meta = paginate(_filtered_hospitals(request), page, page_size)
        return Response({"results": HospitalListSerializer(items, many=True).data, "pagination": meta})

    def post(self, request):
        serializer = HospitalCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        requested_code = data.pop("code", None)

        hospital = Hospital(**data)
        hospital.code = _unique_code(requested_code)
        with SetCurrentUser(request):
            hospital.save()

        return Response(HospitalDetailSerializer(hospital).data, status=201)


class HospitalDetailView(APIView):
    authentication_classes = [InternalServiceAuthentication]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD"):
            return [IsAuthenticated()]
        return [IsStaffOrSuperuser()]

    def get_object(self, pk):
        return (
            Hospital.nondeleted_objects.select_related(
                "ownership", "owner", "province", "regency", "district", "village"
            )
            .prefetch_related("hospitalprofessional_set", "hospitalbed_set", "hospitalservice_set")
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):
        hospital = self.get_object(pk)
        if hospital is None:
            return Response(status=404)
        return Response(HospitalDetailSerializer(hospital).data)

    def head(self, request, pk):
        # Backs hiveforest-api's get_active_by_id() - a lightweight existence probe
        # for callers (soft-delete, bulk update) that don't need the full detail payload.
        exists = Hospital.nondeleted_objects.filter(pk=pk).exists()
        return Response(status=200 if exists else 404)

    def patch(self, request, pk):
        hospital = Hospital.nondeleted_objects.filter(pk=pk).first()
        if hospital is None:
            return Response(status=404)

        serializer = HospitalWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        requested_code = data.pop("code", None)

        for field, value in data.items():
            setattr(hospital, field, value)
        hospital.code = _unique_code(requested_code)
        with SetCurrentUser(request):
            hospital.save()

        return Response(HospitalDetailSerializer(hospital).data)

    def delete(self, request, pk):
        hospital = Hospital.nondeleted_objects.filter(pk=pk).first()
        if hospital is None:
            return Response(status=404)

        hospital.code = _unique_code(None)
        with SetCurrentUser(request):
            hospital.delete()

        return Response(status=204)


class HospitalExportView(APIView):
    # Same filters as HospitalListView, no pagination - hiveforest-api streams the
    # CSV/Excel response itself, this just hands back every matching row as JSON.
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hospitals = _filtered_hospitals(request)
        return Response({"results": HospitalListSerializer(hospitals, many=True).data})


def _filtered_doctors(request):
    q = request.query_params.get("q")
    specialization = request.query_params.getlist("specialization") or None
    province = request.query_params.getlist("province") or None

    doctors = Doctor.nondeleted_objects.order_by("name")

    if q:
        doctors = doctors.filter(name__icontains=q)
    if specialization:
        doctors = doctors.filter(doctorspeciality__speciality_desc__in=specialization)
    if province:
        doctors = doctors.filter(doctorplace__province__name__in=province)
    if specialization or province:
        doctors = doctors.distinct()

    return doctors.prefetch_related(
        "doctorspeciality_set",
        "doctoreducation_set",
        "doctorplace_set__province",
    )


def _unique_source_id():
    # Mirrors hiveforest-api's DoctorRepository._unique_source_id(): source_id is
    # unique on the model, so every doctor created here needs a fresh value.
    return f"API-{uuid.uuid4().hex[:12]}"


class DoctorListView(APIView):
    authentication_classes = [InternalServiceAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsStaffOrSuperuser()]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        items, meta = paginate(_filtered_doctors(request), page, page_size)
        return Response({"results": DoctorListSerializer(items, many=True).data, "pagination": meta})

    def post(self, request):
        serializer = DoctorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        name = data.pop("name")

        # Doctor.save() (below) unconditionally does `self.code =
        # "-".join([self.person.name, self.license])`, which crashes with
        # AttributeError if person is None - so every doctor created here needs a
        # minimal Person first. first_name is truncated to Person's own 50-char
        # column limit; the full name is kept untruncated on Person.name/Doctor.name.
        with SetCurrentUser(request):
            person = Person.objects.create(name=name, first_name=name[:50])
            doctor = Doctor(person=person, name=name, source_id=_unique_source_id(), **data)
            doctor.save()

        return Response(DoctorDetailSerializer(doctor).data, status=201)


class DoctorDetailView(APIView):
    authentication_classes = [InternalServiceAuthentication]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD"):
            return [IsAuthenticated()]
        return [IsStaffOrSuperuser()]

    def get_object(self, pk):
        return (
            Doctor.nondeleted_objects.prefetch_related(
                Prefetch("doctorplace_set", queryset=DoctorPlace.objects.select_related("province", "city")),
                "doctoreducation_set",
                "doctorspeciality_set",
            )
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):
        doctor = self.get_object(pk)
        if doctor is None:
            return Response(status=404)
        return Response(DoctorDetailSerializer(doctor).data)

    def head(self, request, pk):
        exists = Doctor.nondeleted_objects.filter(pk=pk).exists()
        return Response(status=200 if exists else 404)

    def patch(self, request, pk):
        doctor = Doctor.nondeleted_objects.filter(pk=pk).first()
        if doctor is None:
            return Response(status=404)

        serializer = DoctorWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(doctor, field, value)
        with SetCurrentUser(request):
            doctor.save()

        return Response(DoctorDetailSerializer(doctor).data)

    def delete(self, request, pk):
        doctor = Doctor.nondeleted_objects.filter(pk=pk).first()
        if doctor is None:
            return Response(status=404)

        with SetCurrentUser(request):
            doctor.delete()

        return Response(status=204)


class DoctorDashboardView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        top_n = int(request.query_params.get("top_n", 8))

        counts = Doctor.nondeleted_objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=1)),
            inactive=Count("id", filter=Q(status=0)),
        )

        # Filters directly on the FK's own soft-delete flag instead of joining through
        # Doctor.nondeleted_objects, which would compile a subquery against the full
        # ~280k-row Doctor table on every call.
        active_doctor = Q(doctor__dat__isnull=True)
        facility_counts = DoctorPlace.objects.filter(active_doctor).aggregate(
            facilities=Count("place_desc", filter=~Q(place_desc=""), distinct=True),
            regions=Count("province", distinct=True),
        )

        top_places = (
            DoctorPlace.objects.filter(active_doctor)
            .exclude(place_desc="")
            .values("place_desc")
            .annotate(doctor_count=Count("doctor", distinct=True))
            .order_by("-doctor_count")[:top_n]
        )
        top_specialities = (
            DoctorSpeciality.objects.filter(active_doctor)
            .exclude(speciality_desc="")
            .values("speciality_desc")
            .annotate(doctor_count=Count("doctor", distinct=True))
            .order_by("-doctor_count")[:top_n]
        )
        top_education = (
            DoctorEducation.objects.filter(active_doctor)
            .exclude(institution__isnull=True)
            .exclude(institution="")
            .values("institution")
            .annotate(doctor_count=Count("doctor", distinct=True))
            .order_by("-doctor_count")[:top_n]
        )

        return Response(
            {
                "stats": {
                    "total": counts["total"] or 0,
                    "active": counts["active"] or 0,
                    "inactive": counts["inactive"] or 0,
                    "facilities": facility_counts["facilities"] or 0,
                    "regions": facility_counts["regions"] or 0,
                },
                "top_places": TopItemSerializer(
                    [{"label": r["place_desc"], "count": r["doctor_count"]} for r in top_places], many=True
                ).data,
                "top_specialities": TopItemSerializer(
                    [{"label": r["speciality_desc"], "count": r["doctor_count"]} for r in top_specialities], many=True
                ).data,
                "top_education": TopItemSerializer(
                    [{"label": r["institution"], "count": r["doctor_count"]} for r in top_education], many=True
                ).data,
            }
        )


class DoctorExportView(APIView):
    authentication_classes = [InternalServiceAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Streamed as newline-delimited JSON (one row array per line) rather than one
        # big JSON body - Doctor has ~280k rows, and hiveforest-api's repository reads
        # this incrementally via httpx's streaming client instead of buffering it all.
        def relation_map(queryset, value_field):
            mapping = {}
            for doctor_id, value in queryset.values_list("doctor_id", value_field):
                if not value:
                    continue
                bucket = mapping.setdefault(doctor_id, [])
                if value not in bucket:
                    bucket.append(value)
            return mapping

        speciality_map = relation_map(DoctorSpeciality.objects.exclude(speciality_desc=""), "speciality_desc")
        education_map = relation_map(
            DoctorEducation.objects.exclude(institution__isnull=True).exclude(institution=""), "institution"
        )
        place_map = relation_map(DoctorPlace.objects.exclude(place_desc=""), "place_desc")
        province_map = relation_map(
            DoctorPlace.objects.annotate(province_name=Coalesce("province__name", "province_desc"))
            .exclude(province_name__isnull=True)
            .exclude(province_name=""),
            "province_name",
        )

        rows_qs = _filtered_doctors(request).values_list(
            "id", "code", "name", "license", "start_year", "start_month", "status"
        )

        def generate():
            for doctor_id, code, name, license_no, start_year, start_month, status in rows_qs.iterator(
                chunk_size=5000
            ):
                start_period = "-"
                if start_year and start_month and 1 <= start_month <= 12:
                    start_period = f"{calendar.month_abbr[start_month]} {start_year}"
                row = [
                    code or "-",
                    name,
                    license_no or "-",
                    ", ".join(speciality_map.get(doctor_id, [])) or "-",
                    start_period,
                    ", ".join(province_map.get(doctor_id, [])) or "-",
                    ", ".join(education_map.get(doctor_id, [])) or "-",
                    ", ".join(place_map.get(doctor_id, [])) or "-",
                    "Active" if status == 1 else "Inactive",
                ]
                yield json.dumps(row) + "\n"

        return StreamingHttpResponse(generate(), content_type="application/x-ndjson")
