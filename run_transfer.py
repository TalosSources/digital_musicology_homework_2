import argparse
import os
import shutil

import music21

from src.data import DATASET_PATH, ROOT_PATH
from src.interpret import interpret
from src.midi_transfers import get_transfer_function_for_corpus


def save_midi(generated_score, original_midi_path, save_audio):
    # save midi
    (ROOT_PATH / "results").mkdir(exist_ok=True, parents=True)

    # write original_midi
    shutil.copy(
        str(original_midi_path), str(ROOT_PATH / "results" / "original_midi.mid")
    )
    # write generated_midi
    generated_score.write("midi", str(ROOT_PATH / "results" / "generated_midi.mid"))

    if save_audio:
        # create wav from midi
        filename = str(ROOT_PATH / "results" / "original_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)

        filename = str(ROOT_PATH / "results" / "generated_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)


def run_transfer(midi_root_path, save_audio):
    xml_path = DATASET_PATH / midi_root_path / "xml_score.musicxml"
    midi_path = DATASET_PATH / midi_root_path / "midi_score.mid"

    generated_score = interpret(midi_path, xml_path)
    save_midi(
        generated_score=generated_score,
        original_midi_path=midi_path,
        save_audio=save_audio,
    )


# OLD Code
# def run_transfer(
#     composer,
#     midi_root_path,
#     save_audio,
# ):
#     (
#         time_transfer_function,
#         velocity_transfer_function,
#     ) = get_transfer_function_for_corpus(composer, exclude_path=midi_root_path)

#     midi_path = DATASET_PATH / midi_root_path / "midi_score.mid"
#     sample_score = music21.converter.parse(midi_path)

#     # time is not supported yet
#     # sample_score = time_transfer_function(sample_score)
#     sample_score = velocity_transfer_function(sample_score)


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Generate Performed MIDI")

    # args.add_argument(
    #     "-c",
    #     "--composer",
    #     default="Schubert",
    #     type=str,
    #     help="Composer Name for corpus creation (default: Bach)",
    # )

    args.add_argument(
        "-m",
        "--midi_root_path",
        default="Schubert/Impromptu_op.90_D.899/3",
        type=str,
        help="Path that will be used for midi_generation (default: Schubert/Impromptu_op.90_D.899/3)",
    )

    args.add_argument(
        "-s",
        "--save_audio",
        default=False,
        type=bool,
        help="Whether to convert midi to wav or not (default: False)",
    )

    args = args.parse_args()

    run_transfer(args.midi_root_path, args.save_audio)
