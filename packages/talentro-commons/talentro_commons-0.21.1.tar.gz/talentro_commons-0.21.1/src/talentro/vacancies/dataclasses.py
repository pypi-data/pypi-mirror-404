from dataclasses import field
from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel
from pydantic import field_validator
from pydantic.dataclasses import dataclass

from .taxanomy import RemoteType, SalaryFrequency, JobCategory, Education, ExperienceLevel, ContractType, IndustryCategory

from ..general.dataclasses import ResolvableCompanyModel
from ..integrations.dataclasses import LinkInfo
from ..services.caching import CacheService
from ..services.clients import MSClient
from ..util.enum import to_enum
from ..util.vacancy import generate_vacancy_hash
from ..vacancies.models import Feed as FeedModel, Vacancy as VacancyModel
from ..vacancies.models import Question as QuestionModel, ApplicationFlow as ApplicationFlowModel, QuestionCategory, \
    ApplicationFlowType


class VacancyLocation(BaseModel):
    zipcode: str | None = None
    city: str | None = None
    address: str | None = None
    state: str | None = None
    country: str | None = None
    lat: float | None = None
    lng: float | None = None


class Salary(BaseModel):
    min: float | None = None
    max: float | None = None
    currency: str | None = None
    frequency: SalaryFrequency | None = None

    @field_validator("frequency", mode="before")
    @classmethod
    def cast_frequency(cls, v):
        return SalaryFrequency(v) if v else None


class Hours(BaseModel):
    min: int | None = None
    max: int | None = None
    fte: float | None = None


class ContactDetails(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    role: str | None = None


class QuestionConfig(BaseModel):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization: Optional[UUID] = None

    application_flow_id: Optional[UUID] = None
    question_category: QuestionCategory
    key: str
    question: Optional[str] = None
    text: Optional[str] = None
    type: str
    required: bool
    options: Optional[list] = []

    @field_validator("question_category", mode="before")
    @classmethod
    def cast_question_category(cls, v):
        return QuestionCategory(v)

    @classmethod
    async def from_model(cls: "QuestionConfig", model: QuestionModel) -> "QuestionConfig":
        return cls(**model.model_dump())


class ApplicationFlowConfig(BaseModel):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization: Optional[UUID] = None

    name: str
    type: ApplicationFlowType
    questions: list[QuestionConfig]

    @field_validator("type", mode="before")
    @classmethod
    def cast_type(cls, v):
        return ApplicationFlowType(v)

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "ApplicationFlowConfig | None":
        cache = CacheService()

        cache_key = f"resolver:org:{organization_id}:application_flow_id:{object_id}"

        if value := await cache.get(cache_key):
            return value

        result = await MSClient.vacancies().get(f"application-flows/{object_id}", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return ApplicationFlowConfig(**result.json())

    @classmethod
    async def from_model(cls: "ApplicationFlowConfig", model: ApplicationFlowModel, questions: list[QuestionModel]) -> "ApplicationFlowConfig":
        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            name=model.name,
            type=ApplicationFlowType(model.type),
            questions=[await QuestionConfig.from_model(question) for question in questions],
        )


class ApplicationFlowInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    type: ApplicationFlowType
    question_count: int
    is_used_in_campaign: bool
    handled_candidates_count: int

    @field_validator("type", mode="before")
    @classmethod
    def cast_type(cls, v):
        return ApplicationFlowType(v)

    @classmethod
    async def from_model(cls: "ApplicationFlowInfo", model: ApplicationFlowModel) -> "ApplicationFlowInfo":
        return cls(
            **model.model_dump(),
            question_count=len(model.questions),
            is_used_in_campaign=False
        )


class RawVacancy(BaseModel):

    # Required fields
    reference_number: str
    requisition_id: str
    title: str
    job_site_url: str
    company_name: str
    publish_date: datetime | None = None

    category: List[JobCategory] = field(default_factory=list)
    experience: List[ExperienceLevel] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    industry_category: List[IndustryCategory] = field(default_factory=list)

    # Connected data
    hours: Hours = field(default_factory=Hours)
    location: VacancyLocation = field(default_factory=VacancyLocation)
    salary: Salary = field(default_factory=Salary)
    recruiter: ContactDetails = field(default_factory=ContactDetails)

    # Optional fields
    description: str | None = None
    status: str | None = None
    parent_company_name: str | None = None
    expiration_date: datetime | None = None
    last_updated_date: datetime | None = None

    remote_type: RemoteType | None = None
    contract_type: ContractType | None = None
    video_url: str | None = None
    applied_sanitizers: List[str] = []

    @field_validator("remote_type", mode="before")
    @classmethod
    def cast_remote_type(cls, v):
        return RemoteType(v) if v else None

    def to_model(self, feed: FeedModel):
        model = VacancyModel(
            feed_id=feed.id,
            organization=feed.organization,
            reference_number=self.reference_number,
            requisition_id=self.requisition_id,
            title=self.title,
            description=self.description,
            status=self.status,
            job_site_url=self.job_site_url,
            company_name=self.company_name,
            parent_company_name=self.parent_company_name,
            remote_type=self.remote_type.value if self.remote_type else None,
            contract_type=self.contract_type.value if self.contract_type else None,
            publish_date=self.publish_date,
            expiration_date=self.expiration_date,
            last_updated_date=self.last_updated_date,
            category=self.category,
            industry_category=self.industry_category,
            experience=self.experience,
            education=self.education,
            hours_fte=self.hours.fte,
            hours_min=self.hours.min,
            hours_max=self.hours.max,
            location_address=self.location.address,
            location_zipcode=self.location.zipcode,
            location_city=self.location.city,
            location_state=self.location.state,
            location_country=self.location.country,
            location_lat=self.location.lat,
            location_lng=self.location.lng,
            salary_min=self.salary.min,
            salary_max=self.salary.max,
            salary_currency=self.salary.currency,
            salary_frequency=self.salary.frequency.value if self.salary.frequency else SalaryFrequency.MONTH,
            recruiter_first_name=self.recruiter.first_name,
            recruiter_last_name=self.recruiter.last_name,
            recruiter_phone_number=self.recruiter.phone_number,
            recruiter_email=self.recruiter.email,
            recruiter_role=self.recruiter.role,
            video_url=self.video_url,
            applied_sanitizers=getattr(self, "applied_sanitizers", []),
        )

        checksum = generate_vacancy_hash(model)
        model.checksum = checksum
        return model


class VacancyConfig(RawVacancy):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    feed_id: UUID
    application_flow_id: Optional[UUID]


class VacancyInfo(RawVacancy):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    feed_id: UUID
    application_flow: Optional["ApplicationFlowConfig"]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "VacancyInfo | None":
        cache = CacheService()

        cache_key = f"resolver:org:{organization_id}:vacancy_id:{object_id}"

        if value := await cache.get(cache_key):
            return value

        result = await MSClient.vacancies().get(f"vacancies/{object_id}/resolve", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return VacancyInfo(**result.json())

    @classmethod
    async def from_model(cls: "VacancyInfo", model: VacancyModel) -> "VacancyInfo":
        if model.application_flow_id:
            application_flow = await ApplicationFlowConfig.resolve_object(model.application_flow_id, model.organization)
        else:
            application_flow = None

        hours = Hours(
            min=model.hours_min,
            max=model.hours_max,
            fte=model.hours_fte,
        )

        location = VacancyLocation(
            address=getattr(model, "location_address", None),
            zipcode=getattr(model, "location_zipcode", None),
            city=getattr(model, "location_city", None),
            state=getattr(model, "location_state", None),
            country=getattr(model, "location_country", None),
            lat=getattr(model, "location_lat", None),
            lng=getattr(model, "location_lng", None),
        )

        salary = Salary(
            min=getattr(model, "salary_min", None),
            max=getattr(model, "salary_max", None),
            currency=getattr(model, "salary_currency", "EUR") or "EUR",
            frequency=to_enum(SalaryFrequency, getattr(model, "salary_frequency", SalaryFrequency.MONTH) or SalaryFrequency.MONTH),
        )

        recruiter = ContactDetails(
            first_name=getattr(model, "recruiter_first_name", None),
            last_name=getattr(model, "recruiter_last_name", None),
            phone_number=getattr(model, "recruiter_phone_number", None),
            email=getattr(model, "recruiter_email", None),
            role=getattr(model, "recruiter_role", None),
        )

        remote_type = to_enum(RemoteType, getattr(model, "remote_type", None))

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            feed_id=model.feed_id,
            application_flow=application_flow,

            reference_number=model.reference_number,
            requisition_id=model.requisition_id,
            title=model.title,
            description=model.description,
            job_site_url=model.job_site_url,
            company_name=model.company_name,
            publish_date=model.publish_date,

            contract_type=to_enum(ContractType, getattr(model, "contract_type", ContractType.UNSPECIFIED)),

            category=[to_enum(JobCategory, category) for category in model.category or []],
            experience=[to_enum(ExperienceLevel, experience) for experience in model.experience or []],
            education=[to_enum(Education, education) for education in model.education or []],
            industry_category=[to_enum(IndustryCategory, industry_category) for industry_category in model.industry_category or []],

            hours=hours,
            location=location,
            salary=salary,
            recruiter=recruiter,

            status=model.status,
            parent_company_name=model.parent_company_name,
            remote_type=remote_type,
            video_url=model.video_url,
            expiration_date=model.expiration_date,
            last_updated_date=model.last_updated_date,

            applied_sanitizers=getattr(model, "applied_sanitizers", []),
        )

# Feed object
@dataclass
class CustomMappingValue:
    key: str
    field: str
    regex: str | None = None
    preview: str | None = None


@dataclass
class CustomMapping:
    return_pattern: str
    values: List[CustomMappingValue]


@dataclass
class Mapping:
    id: str
    field: str
    type: Literal['mapped', 'custom']
    value: str | None = None
    default: str | None = None
    custom_mapping: CustomMapping | None = None


class FeedInfo(ResolvableCompanyModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    status: str
    file_url: Optional[str]
    entrypoint: Optional[str]
    ats_link: Optional[LinkInfo]
    source_type: str
    last_sync_date: Optional[datetime]
    synced_vacancy_count: int
    sanitation_options: Optional[dict]
    mapping: List[Mapping]
    custom_fields: List[Mapping]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "FeedInfo | None":
        cache = CacheService()

        cache_key = f"resolver:org:{organization_id}:feed_id:{object_id}"

        if value := await cache.get(cache_key):
            return value

        result = await MSClient.vacancies().get(f"feeds/{object_id}/resolve", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return FeedInfo(**result.json())

    @classmethod
    async def from_model(cls: "FeedInfo", model: FeedModel) -> "FeedInfo":
        ats_link = await LinkInfo.resolve_object(model.ats_link_id, model.organization) if model.ats_link_id else None

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            name=model.name,
            status=model.status,
            file_url=model.file_url,
            ats_link=ats_link,
            entrypoint=model.entrypoint,
            source_type=model.source_type,
            last_sync_date=model.last_sync_date,
            synced_vacancy_count=model.synced_vacancy_count,
            sanitation_options=model.sanitation_options,
            mapping=model.mapping,
            custom_fields=model.custom_fields,
        )


class FeedConfig(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    name: str
    status: str
    file_url: Optional[str]
    entrypoint: Optional[str]
    source_type: str
    ats_link_id: Optional[UUID]
    last_sync_date: Optional[datetime]
    synced_vacancy_count: int
    sanitation_options: Optional[dict]
    mapping: List[Mapping]
    custom_fields: List[Mapping]

    @classmethod
    async def from_model(cls: "FeedConfig", model: FeedModel) -> "FeedConfig":
        return cls(**model.model_dump())
