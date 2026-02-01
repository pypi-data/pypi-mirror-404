# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-3-Clause license.
# See LICENSE.openenv in this directory for the full license text.
"""Type definitions from OpenEnv."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ObsT = TypeVar("ObsT")
StateT = TypeVar("StateT")


@dataclass
class StepResult(Generic[ObsT]):
    """Result of one environment step.

    Attributes:
        observation: The environment's observation after the action.
        reward: Scalar reward for this step.
        done: Whether the episode is finished.
    """

    observation: ObsT
    reward: float | None = None
    done: bool = False


class Action(BaseModel):
    """Base class for environment actions."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the action"
    )


class Observation(BaseModel):
    """Base class for environment observations."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    done: bool = Field(default=False, description="Whether the episode has terminated")
    reward: bool | int | float | None = Field(
        default=None, description="Reward signal from the last action"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the observation"
    )


class State(BaseModel):
    """Base class for environment state."""

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    episode_id: str | None = Field(
        default=None, description="Unique identifier for the current episode"
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="Number of steps taken in the current episode",
    )
