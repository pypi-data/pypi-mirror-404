from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from talentro.acquisition.dataclasses import CampaignInfo, AdInfo
from talentro.candidates.models import Application as ApplicationModel, Document as DocumentModel, \
    Candidate as CandidateModel, Source as SourceModel, ExternalLink as ExternalLinkModel
from talentro.integrations.dataclasses import LinkInfo
from talentro.services.caching import CacheService
from talentro.services.clients import MSClient
from talentro.vacancies.dataclasses import VacancyInfo


class CandidateInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

    @classmethod
    async def from_model(cls: "CandidateInfo", model: CandidateModel) -> 'CandidateInfo':
        return CandidateInfo(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone_number=model.phone_number,
            city=model.city,
            country=model.country,
        )


class ApplicationData(BaseModel):
    status: str
    source: str
    candidate_id: UUID
    vacancy_reference_number: str
    screening_answers: dict


class Application(ApplicationData):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID


class DocumentInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    type: str
    blob_name: str

    @classmethod
    async def from_model(cls: "DocumentInfo", model: DocumentModel) -> 'DocumentInfo':
        return DocumentInfo(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            type=model.type,
            blob_name=model.blob_name
        )


class SourceInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    campaign: Optional[CampaignInfo]
    ad: Optional[AdInfo]

    application_count: Optional[int]

    @classmethod
    async def from_model(cls: "SourceInfo", model: SourceModel, application_count: int) -> 'SourceInfo':
        if model.campaign_id:
            campaign = await CampaignInfo.resolve_object(model.campaign_id, model.organization)
        else:
            campaign = None

        if model.ad_id:
            ad = await AdInfo.resolve_object(model.ad_id, model.organization)
        else:
            ad = None

        return SourceInfo(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,
            campaign=campaign,
            ad=ad,
            application_count=application_count,
        )

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "SourceInfo | None":
        cache = CacheService()

        cache_key = f"resolver:org:{organization_id}:source_id:{object_id}"

        if value := await cache.get(cache_key):
            return value

        result = await MSClient.candidates().get(f"sources/{object_id}/resolve", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return SourceInfo(**result.json())


class ApplicationInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    status: str
    screening_answers: dict

    source: Optional[SourceInfo]
    vacancy: Optional[VacancyInfo]
    candidate: Optional[CandidateInfo]

    documents: list[DocumentInfo]
    external_links: list["ExternalLinkInfo"]

    @staticmethod
    async def resolve_object(object_id: UUID, organization_id: UUID) -> "ApplicationInfo | None":
        cache = CacheService()

        cache_key = f"resolver:org:{organization_id}:application_id:{object_id}"

        if value := await cache.get(cache_key):
            return value

        result = await MSClient.candidates().get(f"applications/{object_id}", headers={"X-Organization-ID": str(organization_id)})

        if result.status_code != 200:
            return None

        return ApplicationInfo(**result.json())

    @classmethod
    async def from_model(cls: "ApplicationInfo", model: ApplicationModel) -> 'ApplicationInfo':
        if model.source:
            source = await SourceInfo.resolve_object(model.source.id, model.organization)
        else:
            source = None

        if model.vacancy_id:
            vacancy = await VacancyInfo.resolve_object(model.vacancy_id, model.organization)
        else:
            vacancy = None

        if model.candidate:
            candidate = await CandidateInfo.from_model(model.candidate)
        else:
            candidate = None

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            screening_answers=model.screening_answers,
            status=model.status,

            source=source,
            vacancy=vacancy,
            candidate=candidate,

            documents=[await DocumentInfo.from_model(document) for document in model.documents],
            external_links=[await ExternalLinkInfo.from_model(link) for link in model.external_links],
        )


class ExternalLinkInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    organization: UUID

    link: Optional[LinkInfo]
    external_id: Optional[str]
    external_url: Optional[str]
    status: str
    application_id: UUID

    @classmethod
    async def from_model(cls: "ExternalLinkInfo", model: ExternalLinkModel) -> 'ExternalLinkInfo':
        if model.link_id:
            link = await LinkInfo.resolve_object(model.link_id, model.organization)
        else:
            link = None

        return cls(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            organization=model.organization,

            link=link,
            status=model.status,
            external_id=model.external_id,
            external_url=model.external_url,
            application_id=model.application_id,
        )
