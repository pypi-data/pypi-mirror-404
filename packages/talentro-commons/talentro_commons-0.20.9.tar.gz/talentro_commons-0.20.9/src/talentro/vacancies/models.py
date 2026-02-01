from datetime import datetime
from enum import StrEnum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Column, JSON, UniqueConstraint, Enum
from sqlmodel import Field, Relationship

from ..general.models import BaseModel


class SourceType(StrEnum):
    ATS = "ATS"
    CUSTOM_FILE = "CUSTOM_FILE"


class QuestionCategory(StrEnum):
    SCREENING = "SCREENING"
    DEMOGRAPHIC = "DEMOGRAPHIC"


class ApplicationFlowType(StrEnum):
    CONVERSATIONAL = "CONVERSATIONAL"
    QUESTIONNAIRE = "QUESTIONNAIRE"


class VacanciesModel(BaseModel):
    pass


class VacanciesOrganizationModel(VacanciesModel):
    organization: UUID = Field(index=True)


class Feed(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    status: str = Field(index=True)
    file_url: Optional[str] = Field()
    ats_link_id: Optional[UUID] = Field()
    entrypoint: Optional[str] = Field()
    last_sync_date: Optional[datetime] = Field()
    source_type: SourceType =  Field(sa_column=Column(Enum(SourceType)))
    synced_vacancy_count: int = Field(default=0)
    sanitation_options: Optional[dict] = Field(sa_column=Column(JSON), default=None)
    mapping: list = Field(sa_column=Column(JSON))
    custom_fields: list = Field(sa_column=Column(JSON))

    vacancies: list["Vacancy"] = Relationship(back_populates="feed")


class Vacancy(VacanciesOrganizationModel, table=True):
    feed_id: UUID = Field(foreign_key="feed.id", ondelete="CASCADE", index=True)
    feed: "Feed" = Relationship(back_populates="vacancies")

    reference_number: str = Field(index=True)
    requisition_id: str = Field(index=True)
    title: str = Field(index=True)
    description: Optional[str] = Field()
    status: str = Field()
    job_site_url: str = Field()
    company_name: str = Field(index=True)
    parent_company_name: Optional[str] = Field()
    remote_type: Optional[str] = Field()
    publish_date: Optional[datetime] = Field()
    expiration_date: Optional[datetime] = Field()
    last_updated_date: Optional[datetime] = Field()
    category: List[str] = Field(sa_column=Column(JSON))
    experience: List[str] = Field(sa_column=Column(JSON))
    education: List[str] = Field(sa_column=Column(JSON))
    industry_category: List[str] = Field(sa_column=Column(JSON))
    contract_type: Optional[str] = Field()
    hours_fte: Optional[float] = Field()
    hours_min: Optional[int] = Field()
    hours_max: Optional[int] = Field()
    location_address: Optional[str] = Field()
    location_zipcode: Optional[str] = Field()
    location_city: Optional[str] = Field()
    location_state: Optional[str] = Field()
    location_country: Optional[str] = Field()
    location_lat: Optional[float] = Field()
    location_lng: Optional[float] = Field()
    salary_min: Optional[float] = Field()
    salary_max: Optional[float] = Field()
    salary_currency: Optional[str] = Field()
    salary_frequency: Optional[str] = Field()
    recruiter_first_name: Optional[str] = Field()
    recruiter_last_name: Optional[str] = Field()
    recruiter_phone_number: Optional[str] = Field()
    recruiter_email: Optional[str] = Field()
    recruiter_role: Optional[str] = Field()
    video_url: Optional[str] = Field()
    checksum: str = Field(index=True)
    application_flow_id: Optional[UUID] = Field(foreign_key="applicationflow.id", ondelete="SET NULL", index=True, nullable=True)
    application_flow: "ApplicationFlow" = Relationship(back_populates="vacancies")
    applied_sanitizers: List[str] = Field(sa_column=Column(JSON), default_factory=list)

    __table_args__ = (
        UniqueConstraint("feed_id", "reference_number", name="uq_feed_reference"),
    )


class ApplicationFlow(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    type: str = Field()
    handled_candidates_count: Optional[int] = Field(default=0, nullable=True)
    questions: list["Question"] = Relationship(back_populates="application_flow", cascade_delete=True)
    vacancies: list["Vacancy"] = Relationship(back_populates="application_flow")


class Question(VacanciesOrganizationModel, table=True):
    application_flow_id: UUID = Field(foreign_key="applicationflow.id", ondelete="CASCADE", index=True)
    question_category: str = Field()
    key: str = Field(index=True)
    question: Optional[str] = Field()
    text: Optional[str] = Field()
    type: str = Field()
    required: bool = Field()
    options: Optional[list] = Field(sa_column=Column(JSON))
    application_flow: ApplicationFlow = Relationship(back_populates="questions")


class Modification(VacanciesOrganizationModel, table=True):
    name: str = Field(index=True)
    type: str = Field(index=True)
    selection_configuration: dict = Field(sa_column=Column(JSON))
    modification_configuration: dict = Field(sa_column=Column(JSON))

