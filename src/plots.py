import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")


def plot_transfer_function(
    axes,
    midi_beats,
    unperformed_beats,
    performance_beats,
    performance_beats_estimated_dict,
    performance_type="time",
):
    """
    Chart for performance time/velocity vs beats position
    """

    colors = ["#2c7bb6", "#fdae61", "#d7191c", "#abd9e9"]

    # pop the last element from midi beats because we use differences

    if performance_type == "time":
        midi_beats = midi_beats[:-1]
        performance_beats = performance_beats[:-1]
        unperformed_beats = unperformed_beats[:-1]

    # plot unperformed
    axes.plot(
        midi_beats,
        unperformed_beats,
        label="unperformed",
        color=colors[-1],
        linestyle="--",
        linewidth=2,
    )

    # plot performance

    axes.plot(
        midi_beats, performance_beats, label="performed", color=colors[0], linewidth=2
    )

    # plot each estimator
    for i, (k, v) in enumerate(performance_beats_estimated_dict.items()):
        if performance_type == "time":
            v = v[:-1]  # one element is redundant
        axes.plot(midi_beats, v, label=k, color=colors[i + 1], linewidth=2)
    axes.set_xlabel("MIDI Beat Number")
    if performance_type == "time":
        axes.set_ylabel("Beats Time (in BPM)")
    else:
        axes.set_ylabel("Beats Velocity")
    axes.legend()
    return axes


def plot_average_transfer_function(
    axes,
    midi_beats_list,
    unperformed_beats_list,  # velocity_beats_list or midi_beats_list
    performance_beats_list,
    performance_beats_estimated_list_dict,
    performance_type="time",
):
    """
    Plot transfer function averaged over subcorpus
    """

    (
        max_midi_beats,
        mean_unperformed_beats,
        mean_performance_beats,
        mean_performance_beats_estimated_dict,
    ) = average_over_subcorpus(
        midi_beats_list,
        unperformed_beats_list,
        performance_beats_list,
        performance_beats_estimated_list_dict,
        performance_type,
    )

    return plot_transfer_function(
        axes,
        max_midi_beats,
        mean_unperformed_beats,
        mean_performance_beats,
        mean_performance_beats_estimated_dict,
        performance_type,
    )


def average_over_subcorpus(
    midi_beats_list,
    unperformed_beats_list,
    performance_beats_list,
    performance_beats_estimated_list_dict,
    performance_type,
):
    max_length = 0
    max_midi_beats = []
    for midi_beats in midi_beats_list:
        midi_beats_length = int(midi_beats[-1] / 0.5) + 1
        if midi_beats_length > max_length:
            max_length = midi_beats_length

    max_midi_beats = [0.5 * i for i in range(max_length)]

    sum_performance_beats = np.zeros(max_length)
    amount_performance_beats = np.zeros(max_length)
    for midi_beats, performance_beats in zip(midi_beats_list, performance_beats_list):
        # not all midi beats start from the same beat
        start_position = int(midi_beats[0] / 0.5)
        if performance_type == "time":
            # convert position in seconds to bpm
            performance_beats = 60 / np.diff(np.array(performance_beats))
        sum_performance_beats[
            start_position : start_position + len(performance_beats)
        ] += np.array(performance_beats)
        amount_performance_beats[
            start_position : start_position + len(performance_beats)
        ] += np.ones(len(performance_beats))
    mean_performance_beats = sum_performance_beats / amount_performance_beats

    sum_unperformed_beats = np.zeros(max_length)
    amount_unperformed_beats = np.zeros(max_length)
    for midi_beats, unperformed_beats in zip(midi_beats_list, unperformed_beats_list):
        start_position = int(midi_beats[0] / 0.5)
        if performance_type == "time":
            # convert position in seconds to bpm
            unperformed_beats = 60 / np.diff(np.array(unperformed_beats))
        sum_unperformed_beats[
            start_position : start_position + len(unperformed_beats)
        ] += np.array(unperformed_beats)
        amount_unperformed_beats[
            start_position : start_position + len(unperformed_beats)
        ] += np.ones(len(unperformed_beats))
    mean_unperformed_beats = sum_unperformed_beats / amount_unperformed_beats

    mean_performance_beats_estimated_dict = {}
    for (
        k,
        performance_beats_estimated_list,
    ) in performance_beats_estimated_list_dict.items():
        sum_performance_beats_estimated = np.zeros(max_length)
        amount_performance_beats_estimated = np.zeros(max_length)
        for midi_beats, performance_beats in zip(
            midi_beats_list, performance_beats_estimated_list
        ):
            start_position = int(midi_beats[0] / 0.5)
            sum_performance_beats_estimated[
                start_position : start_position + len(performance_beats)
            ] += np.array(performance_beats)
            amount_performance_beats_estimated[
                start_position : start_position + len(performance_beats)
            ] += np.ones(len(performance_beats))
        mean_performance_beats_estimated = (
            sum_performance_beats_estimated / amount_performance_beats_estimated
        )
        mean_performance_beats_estimated_dict[k] = mean_performance_beats_estimated

    return (
        max_midi_beats,
        mean_unperformed_beats,
        mean_performance_beats,
        mean_performance_beats_estimated_dict,
    )


def plot_beat_frequencies(results, figsize=(15, 4)):
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    for ax, res in zip(axes, results):
        beats, sig = res
        beat_locations, beat_frequencies = beats
        ax.plot(beat_locations, beat_frequencies, color="blue")
        ax.set_xlabel("Onset in Measure (in quarter notes)")
        ax.set_ylabel("Average relative frequency")
        ax.set_title(f"Time signature: {sig}")
        ax.set_xlim(0, 4 * sig[0] / sig[1])
        ax.set_ylim(0, beat_frequencies.max() * 1.25)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(0.5))
    fig.tight_layout()


def plot_composer_and_style(composers, styles, expr_by_composer, expr_by_style):
    fig, (ax_comp, ax_style) = plt.subplots(1, 2, figsize=(15, 5))
    ax_comp.barh(composers, expr_by_composer)
    ax_style.barh(styles, expr_by_style)
    ax_comp.invert_yaxis()
    ax_style.invert_yaxis()
    fig.tight_layout()
    plt.savefig("plots/composer_and_styles.pdf", dpi=600)


def plot_violins(dataframe: pd.DataFrame, title: str, limits: tuple = None, axes=None):
    sns.violinplot(data=dataframe, x="Beat", y="Deviation", ax=axes)
    axes.set_title(f"{title}")
    axes.set_xlabel("Beat Number")
    if limits:
        axes.set_ylim(limits)
    axes.set_ylabel("Deviation from IOI-Duration [%]")
