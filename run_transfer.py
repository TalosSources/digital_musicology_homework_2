import argparse
import os
import shutil

import music21

from src.data import DATASET_PATH, ROOT_PATH
from src.interpret import interpret


def save_midi(original_xml_path, original_midi_path, save_audio):
    # save midi
    save_path = ROOT_PATH / "results"

    # write original_midi
    xml_score: music21.stream.Score = music21.converter.parse(original_xml_path)
    xml_score.write("midi", str(save_path / "xml_midi.mid"))

    shutil.copy(str(original_midi_path), str(save_path / "original_midi.mid"))
    # write generated_midi
    # is is done in interpret itself

    if save_audio:
        # create wav from midi
        filename = str(save_path / "original_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)

        filename = str(save_path / "xml_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)

        filename = str(save_path / "generated_midi")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)

        filename = str(save_path / "generated_midi_with_pedal")
        cmd = f"fluidsynth -ni font.sf2 {filename}.mid -F {filename}.wav -r 16000 > /dev/null"
        os.system(cmd)


def run_transfer(midi_root_path, save_audio):
    xml_path = DATASET_PATH / midi_root_path / "xml_score.musicxml"
    midi_path = DATASET_PATH / midi_root_path / "midi_score.mid"

    performed_midi_paths = []
    performed_midis = os.listdir(str(DATASET_PATH / midi_root_path))
    for performed_midi_name in performed_midis:
        if not performed_midi_name.endswith("mid"):
            continue
        if performed_midi_name == "midi_score.mid":
            continue
        performed_midi_path = DATASET_PATH / midi_root_path / performed_midi_name
        performed_midi_paths.append(str(performed_midi_path))

    interpret(str(midi_path), str(xml_path), performed_midi_paths)
    save_midi(
        original_xml_path=xml_path,
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
