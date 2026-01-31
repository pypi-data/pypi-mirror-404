from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="JobSubmitResponse")


@_attrs_define
class JobSubmitResponse:
    """Response model for job submission.

    Attributes:
        job_id (str):
        status (str):
        poll_url (str):
        country (str):
        version (str):
    """

    job_id: str
    status: str
    poll_url: str
    country: str
    version: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id = self.job_id

        status = self.status

        poll_url = self.poll_url

        country = self.country

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "job_id": job_id,
                "status": status,
                "poll_url": poll_url,
                "country": country,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_id = d.pop("job_id")

        status = d.pop("status")

        poll_url = d.pop("poll_url")

        country = d.pop("country")

        version = d.pop("version")

        job_submit_response = cls(
            job_id=job_id,
            status=status,
            poll_url=poll_url,
            country=country,
            version=version,
        )

        job_submit_response.additional_properties = d
        return job_submit_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
