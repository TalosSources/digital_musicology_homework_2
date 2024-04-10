import os
import re
import xml.etree.ElementTree as ET
from pathlib import PosixPath
from typing import Union

import music21
import numpy as np
import pandas as pd
import tqdm
from pandas import DataFrame
from scipy.stats import levene

from src.data import DATASET_PATH, get_composer_pieces, get_events_table_from_score


def compute_average_distribution(score_paths, sig=(4, 4), subdivision=4):
    """
    Computes the average distribution over several pieces of (sounded) onsets on the beats given predefined beat locations.
    Returns a numpy array with the normalized averaged frequencies
    """

    beat_locations = [
        (i * 4) / (subdivision * sig[1]) for i in range(sig[0] * subdivision)
    ]

    beat_frequencies = None
    for score_path in score_paths:
        freq = compute_distribution(score_path, beat_locations)
        if beat_frequencies is None:
            beat_frequencies = freq
        else:
            beat_frequencies += freq

    beat_frequencies /= len(score_paths)

    return beat_locations, beat_frequencies


def compute_distribution(score_path, beat_locations):
    """
    Computes the distribution in one piece of (sounded) onsets on the beats given predefined beat locations.
    Returns a numpy array with the normalized frequencies
    """

    sample_score = music21.converter.parse(score_path)
    # sample_score.show("midi")
    events = get_events_table_from_score(sample_score)

    onsets = filter_onsets(events, beat_locations)
    # print(f"unique onsets : {set(onsets)}")

    # onset_count = 0 # commented for now because they are not used
    # beat_per_measure = 4

    beat_frequencies = []
    for loc in beat_locations:
        beat_frequencies.append((onsets.count(loc) / len(onsets)))

    return np.array(beat_frequencies)


def find_expressive_timing():  # TODO : arguments
    """
    This function should find where expressive timing happens given an annotations.txt file, and signature info
    A way to do it could be to find beats where the distance to the preceding and following beats aren't the same
    (indicating local slowing/accelerating)
    We could also find the average tempo of the performance and compare inter-beat distance to that average
    But that wouldn't be robust to a piece having several tempis or something
    It could return, for each beat of the measure, a number (percentage?) indicating how "likely" or "intense" expressive timings are there
    Also, I need (TODO) to support such analyses over several measures (for the above methods also)
    """


def filter_onsets(events: DataFrame, beat_locations):
    """
    Extracts the onsets from the events and filter to exclude:
    - unsounded events
    - tied events that started previously
    - events that aren't on the studied grid (we need to justify this assumption of discarding too_precise/fractional/off-measure events)
    """
    sounded_mask = events["event_type"] == "sounded"
    tie_mask = (events["tie_info"] != "tie_stop") & (
        events["tie_info"] != "tie_continue"
    )
    onsets = events[sounded_mask & tie_mask]["onset_in_measure"]
    onsets = onsets[onsets.isin(beat_locations)]
    return onsets.tolist()


def list_all_time_signatures(corpus):
    sigs = [
        extract_time_signature_from_xml(corpus / piece / "xml_score.musicxml")
        for piece in os.listdir(corpus)
    ]
    return set(sigs)


def get_average_distribution_given_time_signature(corpus, time_signature, subdivision):
    """
    This function extracts all pieces with a specific time signature (ex. 4/4) from a corpus and
    computes the average distribution for them
    """
    matching_pieces = [
        piece
        for piece in os.listdir(corpus)
        if extract_time_signature_from_xml(corpus / piece / "xml_score.musicxml")
        == time_signature
    ]
    score_paths = [corpus / piece / "midi_score.mid" for piece in matching_pieces]
    print(f"Time signature {time_signature} is present in {len(score_paths)} pieces.")
    return compute_average_distribution(
        score_paths, sig=time_signature, subdivision=subdivision
    )


def calculate_inter_onset_intervals(annotation: pd.DataFrame, beats: int) -> pd.Series:
    """
    annotation: dataframe of the annotation file
    beats: indication how many beats in a bar. e.g. 3 in 3/4
    output: series containing time passed since last downbeat
    ex. [1,2,3,4,5,6] -> [1,2,3,1,2,3] in a 3/4 pattern
    """

    # OLD IMPLEMENTATION
    # create array containing time of last downbeat
    # bar_onsets = beats * [0]
    # for time, beat in zip(annotation.iloc[:,0], annotation.iloc[:,2]):
    #     # time of last downbeat
    #     if 'db' in beat:
    #         bar_onsets += beats * [time]

    # # remove last downbeats (list gets too long)
    # bar_onsets = bar_onsets[:-beats]
    # # calculate time passed since last downbeat
    # interval_timings = annotation.iloc[:,0] - pd.Series(bar_onsets)

    interval_timings = [0] + [
        annotation.iloc[i, 0] - annotation.iloc[i - 1, 0]
        for i in range(1, len(annotation))
    ]
    interval_timings = pd.Series(interval_timings)

    return interval_timings


def match_regex_for_series(srs: pd.Series, pattern) -> list:
    matched_lines = []
    for idx, info in enumerate(srs):
        match = re.search(pattern, info)
        if match:
            matched_lines.append((idx, match.group(1)))
    return matched_lines


def extract_time_signatures_from_annotation(df: Union[pd.DataFrame, str]) -> list:
    # find all time signatures in beat info series
    if isinstance(df, str):
        df = pd.read_table(df, header=None)
    pattern = r"^db,([0-9]+/[0-9]+)"
    matched_lines = match_regex_for_series(df.iloc[:, 2], pattern)
    time_signatures = []
    for line in matched_lines:
        idx, info = line
        ts = info.split("/")
        ts = [int(x) for x in ts]
        time_signatures.append((idx, ts))
    return time_signatures


def extract_time_signature_from_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()

    # Find the time signature element
    time_signature_element = root.find(".//time")

    if time_signature_element is not None:
        beats_element = time_signature_element.find("beats")
        beat_type_element = time_signature_element.find("beat-type")

        if beats_element is not None and beat_type_element is not None:
            beats = beats_element.text
            beat_type = beat_type_element.text
            return (int(beats), int(beat_type))
        else:
            return "Time signature not found in the XML file."
    else:
        return "Time signature not found in the XML file."


def normalize_interval(srs: pd.Series, beats: int) -> pd.Series:
    ones = srs.index % beats == 1
    normalization_factor = srs.loc[ones].median()
    normalized_series = srs / normalization_factor
    return normalized_series


def annotation_to_inter_onset_intervals(annotation_path: str) -> pd.Series:
    annotation = pd.read_table(annotation_path, header=None)
    ts = extract_time_signatures_from_annotation(annotation)
    onset, time_signature = ts[0]
    beats = time_signature[0]
    inter_onset_interval = calculate_inter_onset_intervals(annotation, beats)
    # skip prelude and always start on first downbeat
    interval = inter_onset_interval.iloc[onset:,].reset_index(drop=True)
    return interval


def get_interval_statistics(interval: pd.Series, beats: int) -> pd.DataFrame:
    """
    Returns the mean and standard deviation of the inter-onset intervals for each beat
    """
    interval_statistics = pd.DataFrame(columns=["mean", "std"])
    for i in range(beats):
        mask = interval.index % beats == i
        beat_timings = interval[mask]
        interval_statistics.loc[i] = [beat_timings.mean(), beat_timings.std()]
    return interval_statistics


def get_levene_test_results(interval: pd.Series, beats: int) -> tuple[float, float]:
    """
    Performs a levene test to check if the variance of the inter-onset intervals is equal for all beats
    """
    samples = []
    for i in range(beats):
        sample = interval[interval.index % beats == i]
        samples.append(sample)
    statistic, p_value = levene(*samples)
    return statistic, p_value


def collect_pieces_with_time_signature(
    subcorpus: PosixPath, time_signature: list[int]
) -> list[str]:
    """
    function that goes through all pieces of a subcorpus and checks if the time signature is the same as provided
    """
    annotations = []
    for piece in subcorpus.iterdir():
        if piece.is_dir():
            for annotation in piece.glob("*_annotations.txt"):
                # exclude the midi score annotations
                if "midi_score_annotations.txt" in str(annotation):
                    continue
                if (
                    extract_time_signatures_from_annotation(str(annotation))[0][1]
                    == time_signature
                ):
                    annotations.append(str(annotation))
    return annotations


def unique_expressiveness_measure(piece):
    """
    Compresses the expressiveness analysis down to a single number for easy inter-style/composer analysis
    given a piece in the form of an annotation path
    """
    interval: pd.Series = annotation_to_inter_onset_intervals(DATASET_PATH / piece)
    stats: DataFrame = get_interval_statistics(interval, 4)
    return stats["std"].mean()


def mean_expressiveness(pieces):
    mean = 0
    piece_count = len(pieces)
    for piece in pieces:
        mean += unique_expressiveness_measure(piece) / piece_count
    return mean


def style_expressiveness_analysis(styles_composers):
    """
    This function computes, for each pre-defined musical style, the average expressiveness metric,
    and compares, report and plot? the results
    styles is a list of list of composers
    NOTE : We weight by performance, but we could also weight by composer or piece
    """
    all_composers = []
    for composers in styles_composers:
        all_composers.extend(composers)
    print(f"all composers = {all_composers}")
    all_pieces = get_composer_pieces(all_composers)  # do this for efficiency
    styles_pieces = [
        all_pieces.loc[all_pieces["composer"].isin(style_composers)][
            "performance_annotations"
        ]
        for style_composers in styles_composers
    ]
    avg_expr = []
    for style_pieces in styles_pieces:
        avg_expr.append(mean_expressiveness(style_pieces))

    return avg_expr


def composer_expressiveness_analysis(composers):
    df = pd.read_csv(DATASET_PATH / "metadata.csv")
    all_pieces = get_composer_pieces(composers, df=df)
    composers_pieces = [
        all_pieces.loc[all_pieces["composer"] == composer]["performance_annotations"]
        for composer in composers
    ]
    avg_expr = []
    for composer_pieces in tqdm.tqdm(composers_pieces, "computing averages:"):
        avg_expr.append(mean_expressiveness(composer_pieces))

    return avg_expr


def combine_beat_deviations(subcorpus: list[str], beat: int) -> list[pd.DataFrame]:
    """
    Combines ioi deviations for each beat in a list of pieces with
    same time signature for later analysis.

    Args:
        subcorpus (list[str]): list of paths to the pieces with same time signature
        beat (int): number of beats in a bar

    Returns:
        list[pd.DataFrame]: list of dataframes with beat and deviation columns
    """
    deviation_per_beat = [[] for _ in range(beat)]

    for piece in subcorpus:
        interval = annotation_to_inter_onset_intervals(piece)
        deviation_from_grid = (interval - interval.median()) / interval.median() * 100
        for i in range(beat):
            deviation_per_beat[i].extend(deviation_from_grid[i::beat].values)

    deviation_per_beat = [pd.Series(lst) for lst in deviation_per_beat]

    data = pd.DataFrame()
    for i, deviation_list in enumerate(deviation_per_beat):
        data = pd.concat(
            [data, pd.DataFrame({"Beat": i, "Deviation": deviation_list})],
            ignore_index=True,
        )

    return data
