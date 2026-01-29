from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class FlowRuleCreate(BaseModel):
    switch: str = Field(..., min_length=1)
    actions: str = Field(..., min_length=1)
    match: Optional[str] = None
    table: Optional[int] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=0, le=65535)
    idle_timeout: Optional[int] = Field(None, ge=0)
    hard_timeout: Optional[int] = Field(None, ge=0)
    cookie: Optional[Union[int, str]] = None
    of_version: Optional[str] = None

    @field_validator("actions")
    @classmethod
    def normalize_actions(cls, value: str) -> str:
        actions = value.strip()
        if actions.lower().startswith("actions="):
            actions = actions.split("=", 1)[1].strip()
        if not actions:
            raise ValueError("actions is required")
        return actions

    @field_validator("match")
    @classmethod
    def normalize_match(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        match = value.strip()
        if not match:
            return None
        if "actions=" in match.lower():
            raise ValueError("match must not include actions")
        return match

    @field_validator("cookie")
    @classmethod
    def normalize_cookie(cls, value: Optional[Union[int, str]]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, int):
            if value < 0:
                raise ValueError("cookie must be >= 0")
            return str(value)
        cookie = str(value).strip()
        return cookie or None


class FlowRuleDelete(BaseModel):
    switch: str = Field(..., min_length=1)
    match: Optional[str] = None
    table: Optional[int] = Field(None, ge=0)
    of_version: Optional[str] = None
    strict: bool = False

    @field_validator("match")
    @classmethod
    def normalize_match(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        match = value.strip()
        if not match:
            return None
        if "actions=" in match.lower():
            raise ValueError("match must not include actions")
        return match


def build_flow(rule: FlowRuleCreate) -> str:
    segments = []
    if rule.cookie is not None:
        segments.append(f"cookie={rule.cookie}")
    if rule.table is not None:
        segments.append(f"table={rule.table}")
    if rule.priority is not None:
        segments.append(f"priority={rule.priority}")
    if rule.idle_timeout is not None:
        segments.append(f"idle_timeout={rule.idle_timeout}")
    if rule.hard_timeout is not None:
        segments.append(f"hard_timeout={rule.hard_timeout}")
    if rule.match:
        segments.append(rule.match)
    segments.append(f"actions={rule.actions}")
    return ",".join(segments)


def build_flow_match(rule: FlowRuleDelete) -> Optional[str]:
    segments = []
    if rule.table is not None:
        segments.append(f"table={rule.table}")
    if rule.match:
        segments.append(rule.match)
    if not segments:
        return None
    return ",".join(segments)
