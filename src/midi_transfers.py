import music21

from src.data import *
from src.estimators import get_estimator_predictions
from src.plots import average_over_subcorpus


class MIDITransfer:
    """
    Class for transfering unperformed MIDI to performed one
    """

    def __init__(
        self, midi_beats, performance_beats_estimated, performance_type="time"
    ):
        """
        Args:
            midi_beats: list of unperformed beats (0.5, 1, 1.5, ...)
            performance_beats_estimated: list of estimated performed metrics
                                         (time / velocity) for each beat
            performance_type: type of performance (time / velocity)
        """

        self.midi_beats = midi_beats
        self.performance_beats = performance_beats_estimated
        self.performance_type = performance_type

        self.midi_beat_to_performance = self.create_transfer_dict()

    def create_transfer_dict(self):
        transfer_dict = {}
        for midi_beat, performance_beat in zip(self.midi_beats, self.performance_beats):
            transfer_dict[midi_beat] = performance_beat
        return transfer_dict

    def __call__(self, sample_score):
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
                    if label == "sounded":
                        global_onset = ((measure.measureNumber - 1) * 4) + event.offset

                        # convert onset to beat onset (e.g. 0.75 -> 0.5)
                        # we find the closest beat to the event
                        beat_global_onset = round(global_onset * 2.0) / 2.0

                        if self.performance_type == "velocity":
                            perf_velocity = self.midi_beat_to_performance.get(
                                beat_global_onset, velocity
                            )
                            event.volume.velocity = perf_velocity

        return sample_score


def get_average_transfer_function(
    midi_beats_list,
    unperformed_beats_list,  # velocity_beats_list or midi_beats_list
    performance_beats_list,
    performance_beats_estimated_list_dict,
    performance_type="time",
):
    """
    Get transfer function averaged over subcorpus
    """

    (
        midi_beats,
        unperformed_beats,
        performance_beats,
        performance_beats_estimated_dict,
    ) = average_over_subcorpus(
        midi_beats_list,
        unperformed_beats_list,
        performance_beats_list,
        performance_beats_estimated_list_dict,
        performance_type,
    )

    performance_beats_estimated = performance_beats_estimated_dict["random"]

    if performance_type == "time":
        midi_beats = midi_beats[:-1]
        performance_beats = performance_beats[:-1]
        unperformed_beats = unperformed_beats[:-1]
        performance_beats_estimated = performance_beats_estimated[:-1]

    return MIDITransfer(midi_beats, performance_beats_estimated, performance_type)


def get_transfer_function_for_corpus(
    composer="Bach", exclude_path="Bach/Prelude/bwv_846"
):
    """
    Get transfer function for corpus using random estimator.

    Train estimator on train split. Average over test split.
    Resulting MIDITransfer can be applied to midi score.

    Args:
        composer: str name for subcorpus
        exclude_path: str path for piece which we do not want to use
                      for MIDITransfer creation (do not use in train
                      and averaging). This piece will be
                      used later for MIDI generation. That is, our
                      MIDITransfer will be applied on this piece.

    Returns:
        time_transfer_function: MIDITransfer for time
        velocity_transfer_function: MIDITransfer for velocity
    """

    df, json_data = get_dataset_metadata(composer)
    beats_list_dict = get_midi_performance_pairs(df, json_data, "4/4", exclude_path)
    train_beats_list_dict, test_beats_list_dict = train_test_split(
        beats_list_dict, test_size=0.2
    )

    midi_beats_list = test_beats_list_dict["midi_beats_list"]
    velocity_beats_list = test_beats_list_dict["velocity_beats_list"]
    performance_beats_list = test_beats_list_dict["performance_beats_list"]
    perf_velocity_beats_list = test_beats_list_dict["perf_velocity_beats_list"]

    performance_beats_estimated_list_dict = {}
    perf_velocity_beats_estimated_list_dict = {}

    # random estimate
    (
        performance_beats_estimated_list,
        velocity_beats_estimated_list,
    ) = get_estimator_predictions(
        train_beats_list_dict, test_beats_list_dict, estimator_type="random"
    )

    performance_beats_estimated_list_dict["random"] = performance_beats_estimated_list
    perf_velocity_beats_estimated_list_dict["random"] = velocity_beats_estimated_list

    time_transfer_function = get_average_transfer_function(
        midi_beats_list,
        midi_beats_list,  # unperformed_beats_list
        performance_beats_list,
        performance_beats_estimated_list_dict,
        performance_type="time",
    )

    velocity_transfer_function = get_average_transfer_function(
        midi_beats_list,
        velocity_beats_list,  # unperformed_beats_list
        perf_velocity_beats_list,
        perf_velocity_beats_estimated_list_dict,
        performance_type="velocity",
    )

    return time_transfer_function, velocity_transfer_function
