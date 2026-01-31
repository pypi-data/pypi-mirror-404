"""Game execution and scoring runner."""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from sneks.engine.config.base import Config
from sneks.engine.config.graphics import GraphicsConfig
from sneks.engine.scoring import NormalizedScore
from sneks.engine.world import World
from sneks.games.classic import world as classic_world
from sneks.games.classic.config import ClassicConfig


def run(
    world: type[World],
    config: Config,
    group_scores: bool = True,
) -> list[NormalizedScore]:
    if Config().profile:
        import cProfile
        import pstats

        pr = cProfile.Profile()
        pr.enable()

        result = _run(
            world=world,
            config=config,
            group_scores=group_scores,
        )

        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats("tottime").print_stats(20)

        return result
    else:
        return _run(
            world=world,
            config=config,
            group_scores=group_scores,
        )


def _run(
    world: type[World], config: Config, group_scores: bool
) -> list[NormalizedScore]:
    runs = 0
    scores: list[NormalizedScore] = []

    while runs < config.runs:
        current_world = world(config=config)
        current_world.run()
        score = current_world.score()
        score.sort(key=lambda s: s.total(criteria=world.criteria), reverse=True)
        if config.graphics.display:
            print(f"Run #{runs + 1}")
            NormalizedScore.pretty_print_headers(criteria=world.criteria)
            for s in score:
                s.pretty_print(criteria=world.criteria)
            print()
        scores.extend(score)
        runs += 1
        if runs % (config.runs / 20) == 0:
            print(f"{100 * runs / config.runs}% complete")

    if group_scores:
        grouped_scores = NormalizedScore.group(scores=scores, criteria=world.criteria)
        print("Aggregate scores:")
        NormalizedScore.pretty_print_headers(criteria=world.criteria)
        for s in grouped_scores:
            s.pretty_print(criteria=world.criteria)
        print()
        return grouped_scores
    return scores


def score_offline() -> None:
    batch_size = multiprocessing.cpu_count()
    runs = 0
    scores: list[NormalizedScore] = []
    previous_group: list[NormalizedScore] | None = None

    while True:
        with ProcessPoolExecutor() as executor:
            results = executor.map(score_offline_main, range(batch_size), timeout=20)
            completed = 0
            for result in results:
                try:
                    scores.extend(result)
                    completed += 1
                except TimeoutError:
                    pass

            runs += completed
            print("runs", runs)
            grouped = NormalizedScore.group(
                scores, criteria=classic_world.Classic.criteria
            )
            if isinstance(previous_group, list):
                change = 0
                for i in range(len(grouped)):
                    if previous_group[i].name != grouped[i].name:
                        change = 1
                    else:
                        previous_total = previous_group[i].total(
                            criteria=classic_world.Classic.criteria
                        )
                        grouped_total = grouped[i].total(
                            criteria=classic_world.Classic.criteria
                        )
                        change = max(
                            change,
                            abs(previous_total - grouped_total) / grouped_total
                            if grouped_total != 0
                            else 1.0,
                        )
                print("change %", change)
            previous_group = grouped
            NormalizedScore.pretty_print_headers(
                criteria=classic_world.Classic.criteria
            )
            for s in grouped:
                s.pretty_print(criteria=classic_world.Classic.criteria)


def score_offline_main(batch_id: int) -> list[NormalizedScore]:
    ClassicConfig(
        graphics=GraphicsConfig(
            display=False,
        )
    )
    scores = classic_world.main(group_scores=False, return_scores=True)
    if scores is None:
        raise ValueError
    return scores


if __name__ == "__main__":
    score_offline()
