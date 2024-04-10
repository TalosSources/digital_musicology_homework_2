import json
import math
import re
from pathlib import Path

import music21
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

ROOT_PATH = Path(__file__).absolute().resolve().parent.parent
DATASET_PATH = ROOT_PATH / "data" / "asap-dataset"


def get_dataset_metadata(composer):
    """
    Get subcorpus based on composer name

    Args:
        composer: str with composer name

    Returns:
        df: pd.DataFrame with metainformation for the chosen subcorpus
        json_data: dict with annotations
    """
    df = pd.read_csv(DATASET_PATH / "metadata.csv")
    df = df.loc[df["composer"] == composer]

    with open(DATASET_PATH / "asap_annotations.json") as json_file:
        json_data = json.load(json_file)

    return df, json_data


def get_composer_pieces(composers, df=None):
    """
    composers: list of string
    returns a map between a composer name and a list of performance annotation paths
    TODO (maybe) : remove no-repeat pieces. They shouldn't change the average however
    """
    if df is None:
        df = pd.read_csv(DATASET_PATH / "metadata.csv")
    df = df[["composer", "performance_annotations"]]
    # pieces_map = {}
    # for c in composers:
    #    mask = (df["composer"] == c)
    #    pieces = df.loc[mask]["performance_annotations"]
    #    pieces_map[c] = pieces
    return df.loc[df["composer"].isin(composers)]


def get_midi_performance_pairs(df, json_data, time_signature):
    """
    Loads pairs of midi beats and its performed version

    Args:
        df: pd.DataFrame with metainformation for the chosen subcorpus
        json_data: dict with annotations

    Returns:
        midi_beats_list: list(list) of midi beats
        velocity_beats_list: list(list) of velocities for each beat in performance versions
        performance_beats_list: list(list) of corresponding performance versions
    """
    if (ROOT_PATH / "data" / "midi_beats_list.json").exists():
        with open(ROOT_PATH / "data" / "bpm_list.json", "r") as f:
            bpm_list = json.load(f)
        with open(ROOT_PATH / "data" / "midi_beats_list.json", "r") as f:
            midi_beats_list = json.load(f)
        with open(ROOT_PATH / "data" / "midi_downbeats_list.json", "r") as f:
            midi_downbeats_list = json.load(f)
        with open(ROOT_PATH / "data" / "performance_beats_list.json", "r") as f:
            performance_beats_list = json.load(f)
        with open(ROOT_PATH / "data" / "performance_downbeats_list.json", "r") as f:
            performance_downbeats_list = json.load(f)
        with open(ROOT_PATH / "data" / "velocity_beats_list.json", "r") as f:
            velocity_beats_list = json.load(f)
        with open(ROOT_PATH / "data" / "perf_velocity_beats_list.json", "r") as f:
            perf_velocity_beats_list = json.load(f)

        beats_list_dict = {
            "bpm_list": bpm_list,
            "midi_beats_list": midi_beats_list,
            "midi_downbeats_list": midi_downbeats_list,
            "performance_beats_list": performance_beats_list,
            "performance_downbeats_list": performance_downbeats_list,
            "velocity_beats_list": velocity_beats_list,
            "perf_velocity_beats_list": perf_velocity_beats_list,
        }

        return beats_list_dict

    else:
        return create_midi_performance_pairs(df, json_data, time_signature)


def create_midi_performance_pairs(df, json_data, time_signature):
    """
    Creates pairs of midi beats and its performed version

    Args:
        df: pd.DataFrame with metainformation for the chosen subcorpus
        json_data: dict with annotations
        time_signature: str to filter compositions by time signature

    Returns:
        bpm_list: list(float) of midi bpm of pieces
        midi_beats_list: list(list) of midi beats with type
        midi_downbeats_list: list(list) of midi beats with type
        velocity_beats_list: list(list) of velocities for each beat in midi version
        performance_beats_list: list(list) of corresponding performance versions
        performance_downbeats_list: list(list) of corresponding performance versions
        perf_velocity_beats_list: list(list) of velocities for each beat in performance versions
    """
    bpm_list = []
    midi_beats_list = []
    midi_downbeats_list = []
    velocity_beats_list = []
    performance_beats_list = []
    performance_downbeats_list = []
    perf_velocity_beats_list = []

    for i, row in tqdm(df.iterrows(), total=df.shape[0]):
        performance_path = row["midi_performance"]
        if "Bach/Prelude/bwv_885/" in performance_path:
            continue  # json for this dir is broken (wrong midi beats: 1.42 instead of 0.5)
        ts_dict = json_data[performance_path]["midi_score_time_signatures"]

        if len(ts_dict) == 1:  # filter out pieces with more than one time signature
            ts = ts_dict.popitem()[1][0]  # extract time signature str from dict
            # filter out pieces with other time signatures than the desired one
            if ts == time_signature:
                midi_beats = json_data[performance_path]["midi_score_beats"]
                midi_downbeats = json_data[performance_path]["midi_score_downbeats"]
                performance_beats = json_data[performance_path]["performance_beats"]
                performance_downbeats = json_data[performance_path]["performance_beats"]

                # Get original bpm
                beats_per_measure = int(ts[0])
                measure_duration = midi_downbeats[1] - midi_downbeats[0]
                bpm = 60 * beats_per_measure / measure_duration

                bpm_list.append(bpm)
                midi_beats_list.append(midi_beats)
                midi_downbeats_list.append(midi_downbeats)
                performance_beats_list.append(performance_beats)
                performance_downbeats_list.append(performance_downbeats)

                # Get velocity data
                full_midi_path = DATASET_PATH / row["midi_score"]
                sample_score = music21.converter.parse(full_midi_path)
                velocity_beats = get_velocity_beats_from_score(midi_beats, sample_score)

                full_performance_path = DATASET_PATH / performance_path
                sample_score = music21.converter.parse(full_performance_path)
                perf_velocity_beats = get_velocity_beats_from_score(
                    midi_beats, sample_score
                )

                velocity_beats_list.append(velocity_beats)
                perf_velocity_beats_list.append(perf_velocity_beats)

    # save for later use
    with open(ROOT_PATH / "data" / "bpm_list.json", "w") as f:
        json.dump(bpm_list, f)
    with open(ROOT_PATH / "data" / "midi_beats_list.json", "w") as f:
        json.dump(midi_beats_list, f)
    with open(ROOT_PATH / "data" / "midi_downbeats_list.json", "w") as f:
        json.dump(midi_downbeats_list, f)
    with open(ROOT_PATH / "data" / "performance_beats_list.json", "w") as f:
        json.dump(performance_beats_list, f)
    with open(ROOT_PATH / "data" / "performance_downbeats_list.json", "w") as f:
        json.dump(performance_downbeats_list, f)
    with open(ROOT_PATH / "data" / "velocity_beats_list.json", "w") as f:
        json.dump(velocity_beats_list, f)
    with open(ROOT_PATH / "data" / "perf_velocity_beats_list.json", "w") as f:
        json.dump(perf_velocity_beats_list, f)

    beats_list_dict = {
        "bpm_list": bpm_list,
        "midi_beats_list": midi_beats_list,
        "midi_downbeats_list": midi_downbeats_list,
        "performance_beats_list": performance_beats_list,
        "performance_downbeats_list": performance_downbeats_list,
        "velocity_beats_list": velocity_beats_list,
        "perf_velocity_beats_list": perf_velocity_beats_list,
    }

    return beats_list_dict


# taken from the exercise session
def get_events_table_from_score(sample_score):
    rhythm_data_list = []
    for clef in sample_score.parts:
        global_onset = 0
        clef_name = "NotGiven"
        for measure in clef.getElementsByClass("Measure"):
            for event in measure.recurse():
                label = ""
                velocity = 0
                if isinstance(event, music21.note.Note):
                    label = "sounded"
                    velocity = event.volume.velocity
                if isinstance(event, music21.note.Rest):
                    label = "unsounded"
                try:
                    tie_info = "tie_" + event.tie.type
                except AttributeError:
                    tie_info = ""
                if label != "":
                    global_onset = ((measure.measureNumber - 1) * 4) + event.offset
                    rhythm_data_list.append(
                        (
                            clef_name,
                            measure.measureNumber,
                            label,
                            event.offset,
                            global_onset,
                            event.duration.quarterLength,
                            velocity,
                            tie_info,
                        )
                    )
    rhythm_data_df = pd.DataFrame(
        rhythm_data_list,
        columns=[
            "staff",
            "measure_number",
            "event_type",
            "onset_in_measure",
            "onset_in_score",
            "duration",
            "velocity",
            "tie_info",
        ],
    )
    return rhythm_data_df


def get_velocity_beats_from_score(midi_beats, sample_score):
    rhythm_data_df = get_events_table_from_score(sample_score)

    velocity_beats = []
    for beat in midi_beats:
        onsets_in_score = rhythm_data_df["onset_in_score"]
        condition = (onsets_in_score < beat + 0.5) & (onsets_in_score >= beat - 0.5)
        velocity = rhythm_data_df.loc[condition]["velocity"].mean()
        if math.isnan(velocity):
            velocity = 0
        velocity_beats.append(velocity)
    return velocity_beats


def train_test_split(beats_list_dict, test_size=0.2):
    bpm_list = beats_list_dict["bpm_list"]
    midi_beats_list = beats_list_dict["midi_beats_list"]
    midi_downbeats_list = beats_list_dict["midi_downbeats_list"]
    velocity_beats_list = beats_list_dict["velocity_beats_list"]
    performance_beats_list = beats_list_dict["performance_beats_list"]
    performance_downbeats_list = beats_list_dict["performance_downbeats_list"]
    perf_velocity_beats_list = beats_list_dict["perf_velocity_beats_list"]

    np.random.seed(1)
    test_length = int(len(midi_beats_list) * test_size)
    test_index = np.random.choice(len(midi_beats_list), size=test_length, replace=False)
    full_index = np.ones(len(midi_beats_list))
    full_index[test_index] = 0

    train_bpm_list = []
    train_midi_beats_list = []
    train_midi_downbeats_list = []
    train_velocity_beats_list = []
    train_performance_beats_list = []
    train_performance_downbeats_list = []
    train_perf_velocity_beats_list = []

    test_bpm_list = []
    test_midi_beats_list = []
    test_midi_downbeats_list = []
    test_velocity_beats_list = []
    test_performance_beats_list = []
    test_performance_downbeats_list = []
    test_perf_velocity_beats_list = []

    for i in range(len(midi_beats_list)):
        if full_index[i]:  # train
            train_bpm_list.append(bpm_list[i])
            train_midi_beats_list.append(midi_beats_list[i])
            train_midi_downbeats_list.append(midi_downbeats_list[i])
            train_velocity_beats_list.append(velocity_beats_list[i])
            train_performance_beats_list.append(performance_beats_list[i])
            train_performance_downbeats_list.append(performance_downbeats_list[i])
            train_perf_velocity_beats_list.append(perf_velocity_beats_list[i])
        else:  # test
            test_bpm_list.append(bpm_list[i])
            test_midi_beats_list.append(midi_beats_list[i])
            test_midi_downbeats_list.append(midi_downbeats_list[i])
            test_velocity_beats_list.append(velocity_beats_list[i])
            test_performance_beats_list.append(performance_beats_list[i])
            test_performance_downbeats_list.append(performance_downbeats_list[i])
            test_perf_velocity_beats_list.append(perf_velocity_beats_list[i])

    train_beats_list_dict = {
        "bpm_list": train_bpm_list,
        "midi_beats_list": train_midi_beats_list,
        "midi_downbeats_list": train_midi_downbeats_list,
        "performance_beats_list": train_performance_beats_list,
        "performance_downbeats_list": train_performance_downbeats_list,
        "velocity_beats_list": train_velocity_beats_list,
        "perf_velocity_beats_list": train_perf_velocity_beats_list,
    }

    test_beats_list_dict = {
        "bpm_list": test_bpm_list,
        "midi_beats_list": test_midi_beats_list,
        "midi_downbeats_list": test_midi_downbeats_list,
        "performance_beats_list": test_performance_beats_list,
        "performance_downbeats_list": test_performance_downbeats_list,
        "velocity_beats_list": test_velocity_beats_list,
        "perf_velocity_beats_list": test_perf_velocity_beats_list,
    }

    return train_beats_list_dict, test_beats_list_dict


baroque_composers = ["Bach"]
classical_composers = ["Haydn", "Mozart"]
romantic_composers = [
    "Beethoven",
    "Schubert",
    "Chopin",
    "Glinka",
    "Schumann",
    "Liszt",
    "Brahms",
]
impressionist_composers = ["Debussy", "Ravel"]
late_russian_composers = [
    "Balakirev",
    "Prokofiev",
    "Rachmaninoff",
    "Scriabin",
]
