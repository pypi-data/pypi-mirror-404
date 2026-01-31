"""Scoring system with normalization and criteria flags."""

from dataclasses import dataclass
from enum import IntFlag, auto
from typing import Any


class Criteria(IntFlag):
    """Flags for which scoring metrics to include."""

    AGE = auto()
    CRASHES = auto()
    LENGTH = auto()
    DISTANCE = auto()


@dataclass(frozen=True)
class NormalizedScore:
    """Score normalized to 0-1 range for comparison."""

    name: str
    age: float
    crashes: float
    length: float
    distance: float
    raw: "Score"

    def __repr__(self):
        return (
            f"age': {self.age:.4f}, "
            f"crashes': {self.crashes:.4f}, "
            f"length': {self.length:.4f}, "
            f"distance': {self.distance:.4f}, "
            f"age: {self.raw.age:.4f}, "
            f"crashes: {self.raw.crashes:.4f}, "
            f"length: {self.raw.length:.4f}, "
            f"distance: {self.raw.distance:.4f}, "
            f"name: {self.name}"
        )

    def total(self, criteria: Criteria) -> float:
        total = 0.0
        if Criteria.AGE in criteria:
            total += self.age
        if Criteria.CRASHES in criteria:
            total += self.crashes
        if Criteria.LENGTH in criteria:
            total += self.length
        if Criteria.DISTANCE in criteria:
            total += self.distance
        return total

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "NormalizedScore":
        # Assume types are correct, expect a cast error otherwise
        return NormalizedScore(
            name=dictionary["name"],
            age=float(dictionary["age"]),
            crashes=float(dictionary["crashes"]),
            length=float(dictionary["length"]),
            distance=float(dictionary["distance"]),
            raw=Score(
                name=dictionary["name"],
                age=float(dictionary["raw"]["age"]),
                crashes=float(dictionary["raw"]["crashes"]),
                length=float(dictionary["raw"]["length"]),
                distance=float(dictionary["raw"]["distance"]),
            ),
        )

    @classmethod
    def pretty_print_headers(cls, criteria: Criteria) -> None:
        row = ["Total"]
        if Criteria.AGE in criteria:
            row.append("Age'")
        if Criteria.CRASHES in criteria:
            row.append("Crashes'")
        if Criteria.LENGTH in criteria:
            row.append("Length'")
        if Criteria.DISTANCE in criteria:
            row.append("Distance'")
        if Criteria.AGE in criteria:
            row.append("Age")
        if Criteria.CRASHES in criteria:
            row.append("Crashes")
        if Criteria.LENGTH in criteria:
            row.append("Length")
        if Criteria.DISTANCE in criteria:
            row.append("Distance")
        row.append("Name")

        print(" ".join(f"{col:<10}" for col in row))

    def pretty_print(self, criteria: Criteria) -> None:
        row: list[float | str] = [self.total(criteria=criteria)]
        if Criteria.AGE in criteria:
            row.append(self.age)
        if Criteria.CRASHES in criteria:
            row.append(self.crashes)
        if Criteria.LENGTH in criteria:
            row.append(self.length)
        if Criteria.DISTANCE in criteria:
            row.append(self.distance)
        if Criteria.AGE in criteria:
            row.append(self.raw.age)
        if Criteria.CRASHES in criteria:
            row.append(self.raw.crashes)
        if Criteria.LENGTH in criteria:
            row.append(self.raw.length)
        if Criteria.DISTANCE in criteria:
            row.append(self.raw.distance)
        row.append(self.name)
        print(
            " ".join(
                f"{float(col):<10.4f}" if not isinstance(col, str) else col
                for col in row
            )
        )

    @classmethod
    def group(
        cls, scores: list["NormalizedScore"], criteria: Criteria
    ) -> list["NormalizedScore"]:
        """Group the scores by name, and average them."""
        grouped: dict[str, list[NormalizedScore]] = {}
        for score in scores:
            if score.name not in grouped:
                grouped[score.name] = [score]
            else:
                grouped[score.name].append(score)
        final_scores = [
            NormalizedScore(
                name=group[0].name,
                age=sum(s.age for s in group) / len(group),
                crashes=sum(s.crashes for s in group) / len(group),
                length=sum(s.length for s in group) / len(group),
                distance=sum(s.distance for s in group) / len(group),
                raw=Score(
                    name=group[0].name,
                    age=sum(s.raw.age for s in group) / len(group),
                    crashes=sum(s.raw.crashes for s in group) / len(group),
                    length=sum(s.raw.length for s in group) / len(group),
                    distance=sum(s.raw.distance for s in group) / len(group),
                ),
            )
            for group in grouped.values()
        ]
        final_scores.sort(key=lambda s: s.total(criteria=criteria), reverse=True)
        return final_scores


@dataclass(frozen=True)
class Score:
    """Raw score values before normalization."""

    name: str
    age: float
    crashes: float
    length: float
    distance: float

    def normalize(self, min_score: "Score", max_score: "Score") -> NormalizedScore:
        return NormalizedScore(
            name=self.name,
            age=self.normalize_value(
                value=self.age, min_value=min_score.age, max_value=max_score.age
            ),
            crashes=self.normalize_value(
                value=self.crashes,
                min_value=min_score.crashes,
                max_value=max_score.crashes,
                invert=True,
            ),
            length=self.normalize_value(
                value=self.length,
                min_value=min_score.length,
                max_value=max_score.length,
            ),
            distance=self.normalize_value(
                value=self.distance,
                min_value=min_score.distance,
                max_value=max_score.distance,
            ),
            raw=self,
        )

    @classmethod
    def normalize_value(
        cls, value: float, min_value: float, max_value: float, invert: bool = False
    ) -> float:
        if invert:
            return (min_value - value) / max(1.0, (min_value - max_value))
        else:
            return (value - min_value) / max(1.0, (max_value - min_value))
