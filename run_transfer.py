import argparse
import os
import shutil

import music21

from src.data import DATASET_PATH, ROOT_PATH
from src.midi_transfers import get_transfer_function_for_corpus


def run_transfer(
    composer="Bach",
    midi_root_path="Bach/Prelude/bwv_846",
    output_path="generated_midi.mid",
    generate_audio=False,
):
    (
        time_transfer_function,
        velocity_transfer_function,
    ) = get_transfer_function_for_corpus(composer, exclude_path=midi_root_path)

    midi_path = DATASET_PATH / midi_root_path / "midi_score.mid"
    sample_score = music21.converter.parse(midi_path)

    # time is not supported yet
    # sample_score = time_transfer_function(sample_score)
    sample_score = velocity_transfer_function(sample_score)

    # save midi
    (ROOT_PATH / "results").mkdir(exist_ok=True, parents=True)

    # write original_midi
    shutil.copy(str(midi_path), str(ROOT_PATH / "results" / "original_midi.mid"))
    # write generated_midi
    sample_score.write("midi", str(ROOT_PATH / "results" / output_path))

    if generate_audio:
        # create wav from midi
        filename = str(ROOT_PATH / "results" / "original_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)

        filename = str(ROOT_PATH / "results" / output_path.split(".")[0])
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Generate Performed MIDI")

    args.add_argument(
        "-c",
        "--composer",
        default="Bach",
        type=str,
        help="Composer Name for corpus creation (default: Bach)",
    )

    args.add_argument(
        "-m",
        "--midi_root_path",
        default="Bach/Prelude/bwv_846",
        type=str,
        help="Path that will be used for midi_generation (default: Bach/Prelude/bwv_846)",
    )

    args.add_argument(
        "-o",
        "--output_path",
        default="generated_midi.mid",
        type=str,
        help="Path that will be used as generation output (default: generated_midi.mid)",
    )

    args.add_argument(
        "-g",
        "--generate_audio",
        default=False,
        type=bool,
        help="Whether to convert midi to wav or not (default: False)",
    )

    args = args.parse_args()

    run_transfer(
        args.composer, args.midi_root_path, args.output_path, args.generate_audio
    )
