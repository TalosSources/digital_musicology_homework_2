from fractions import Fraction

import music21
import pretty_midi

import numpy as np

# taken from music21
DEFAULT_VELOCITY = 30

def is_left_hand(element): 
    for i in range(6):
        print(element)
        element = element.activeSite
        if element is None:
            return
    


def is_rh_accompaniement_naive(element: music21.note.Note):
    d: music21.Duration = element.duration
    return d.quarterLength == Fraction(1, 3)

def is_rh_accompaniement_xml(element):
    #print(f"Note duration: {element.duration.quarterLength}, note voice: {element.activeSite.id}")
    return (isinstance(element, music21.note.Note) or isinstance(element, music21.note.Rest)) and isinstance(element.activeSite, music21.stream.Voice) and element.activeSite.id == "2"

def bell_curve_velocity_and_timing(measure, element, offset):
    pos_in_motif = (offset * 3) % 6
    bell_curve = -(pos_in_motif**2) + 5 * pos_in_motif

    # velocity manipulation
    if isinstance(element, music21.note.Note):
        v = element.volume.velocity
        if v is None:
            v = 28
        # I do this because the accompaniment seems to loud on the unperformed midi
        #v -= 10  # think if we need this
        # the 6 8th note motif's velocities form a clear bell curve in many recordings
        velocity_increase = 0.8 * bell_curve
        element.volume.velocity = v + velocity_increase

    # tempo manipulation
    # t = get_current_tempo(score, element.offset)
    base_tempo = 120
    t2 = base_tempo + 3 * bell_curve

    #if (offset * 3) % 24 == 23:  # if we're in the beat just before
    #    # I do this to delay each beat after the last of th 6 8th note,
    #    # as can be clearly heard in Kociuban's performance
    #    # But actually, it's not each beat, it's just before the melody.
    #    # If we can detect the melody, we can do it automatically
    #    t2 = base_tempo - 15

    # setting the new tempo at that offset
    m = music21.tempo.MetronomeMark(number=t2)
    m.offset = offset
    #print(f"inserting tempo change {m} ({t2}) at offset {m.offset}")
    measure.insert(offset, m)

def idea_4(score: music21.stream.Score):
    """
    Add an ascending bell curve shape to velocity
    and speed for accompaniment right-hand 8th notes
    """
    print("start idea4")
    for element in score.recurse():
        if is_rh_accompaniement_xml(element):
            #offset = flat_notes.elementOffset(element)
            offset = element.offset
            bell_curve_velocity_and_timing(score, element, offset)

    for part in score.parts:
        for measure in part.getElementsByClass("Measure"):
            for element in measure.recurse():
                if isinstance(element, music21.note.Note) and is_rh_accompaniement_xml(element):
                    offset = element.offset # Offset in measure => we insert the tempo mark in measure
                    bell_curve_velocity_and_timing(measure, element, offset)
     
    print("end idea4")


def get_tempo_at_offset(score, offset):
    tempo_closest_to_offset = 120
    for event in score.flat.getElementsByClass(music21.tempo.MetronomeMark):
        if event.offset <= offset:
            tempo_closest_to_offset = event.number
        else:
            return tempo_closest_to_offset

def iterate_over_dynamics(score):
    for event in score.flat.getElementsByClass(music21.dynamics.Dynamic):
        print("event", event, event.offset)


def idea_12(score):
    """
    Add smooth transition between volume marks (ex. p and pp)

    Function finds all dynamic marks. Then in linearly descreases/
    increases velocity, so the REAL output volume transition is smooth.
    Change happens if distance to transition is less or equal half of a
    measure
    """
    offsets_in_measure = 8  # time_signature = 4/2

    # get all dynamics in piece
    dynamics_offsets = []
    dynamics = []
    for element in score.recurse():
        if isinstance(element, music21.dynamics.Dynamic):
            measure = element.activeSite
            global_offset = element.offset + measure.offset
            dynamics_offsets.append(global_offset)
            dynamics.append(element)

    # if dynamics_offset - note_offset <= offsets_in_measure / 2
    # decay/increase velocity

    dynamics_index = 0
    out_of_range = False
    for element in score.recurse():
        if out_of_range:
            break
        if isinstance(element, music21.note.Note):
            measure = element.activeSite
            if isinstance(measure, music21.stream.Voice):
                measure = measure.activeSite
            global_offset = element.offset + measure.offset

            dynamic_offset = dynamics_offsets[dynamics_index]
            dynamic = dynamics[dynamics_index]

            # look at next dynamic if note is after current dynamic

            while global_offset >= dynamic_offset:
                dynamics_index += 1
                if dynamics_index >= len(dynamics_offsets):
                    out_of_range = True
                    break
                dynamic_offset = dynamics_offsets[dynamics_index]
                dynamic = dynamics[dynamics_index]

            if out_of_range:
                break

            if dynamic_offset - global_offset <= offsets_in_measure / 2:
                note_context = element.volume.getDynamicContext()
                old_velocity = element.volume.velocity

                dynamic_ratio = dynamic.volumeScalar / note_context.volumeScalar

                new_velocity = dynamic_ratio * old_velocity

                offset_ratio = (dynamic_offset - global_offset) / (
                    offsets_in_measure / 2
                )

                new_velocity = (
                    offset_ratio * old_velocity + (1 - offset_ratio) * new_velocity
                )

                element.volume.velocity = new_velocity

def idea_13(unperformed_midi, performed_midi):
    # Extract notes from MIDI
    unperf_notes = unperformed_midi.instruments[0].notes + unperformed_midi.instruments[1].notes
    perf_notes = performed_midi.instruments[0].notes

    # Obtain list of pitches and of (unperformed) velocities
    pitches = set([note.pitch for note in unperf_notes])
    velocities = list(set([note.velocity for note in unperf_notes]))

    # Construct dictionaries of performed and unperformed notes divided according to pitch
    perf_dict = dict()
    unperf_dict = dict()
    for pitch in pitches:
        perf_dict[pitch] = sorted([note for note in perf_notes if note.pitch == pitch], key=lambda x: x.start)
        unperf_dict[pitch] = sorted([note for note in unperf_notes if note.pitch == pitch], key=lambda x: x.start)

    # Construct dictionary of performed notes divided according to their unperformed velocity 
    # (this is to divide notes according to dynamics information in the score: pp, p, f, etc.)
    notes = {k: [] for k in velocities}
    for vel in velocities:
        for pitch in pitches:
            if len(perf_dict[pitch]) > len(unperf_dict[pitch]):
                notes[vel].extend([unperf_dict[pitch][i] for i in range(len(unperf_dict[pitch])) if perf_dict[pitch][i].velocity == vel])
            else:
                notes[vel].extend([unperf_dict[pitch][i] for i in range(len(perf_dict[pitch])) if perf_dict[pitch][i].velocity == vel])
    
    # Compute mean and standard deviation of notes depending on their unperformed velocity
    avg_vel = {vel: np.mean([note.velocity for note in notes[vel]]) for vel in velocities}
    std_vel = {vel: np.std([note.velocity for note in notes[vel]]) for vel in velocities}

    return avg_vel, std_vel

def overwrite_velocities(score: music21.stream.Score):
    to_remove = []
    right_hand_dynamics = [(127 * 0.25, 0)]
    current_dynamic_index = -1
    already_reset = False
    for element in score.recurse():
        #print("elem", element)
        if isinstance(element, music21.dynamics.Dynamic) or isinstance(element, music21.dynamics.DynamicWedge):
            to_remove.append(element)
            print("remomving")
            if isinstance(element, music21.dynamics.Dynamic) and element.activeSite.activeSite == score.parts[0]:
                #if element.value != 'ppp':
                print("appending!!!!!!!!!!!!!!!")
                right_hand_dynamics.append((127 * element.volumeScalar, element.getOffsetInHierarchy(score)))

                print("encountered at rh ", element.value, element.volumeScalar, "dynamic becomes", right_hand_dynamics[current_dynamic_index][0])
                #else:
                #    print("removed ppp at ", element.offset)
            else:
                print("element", element)
                print("active site", element.activeSite.activeSite)
        elif isinstance(element, music21.note.Note) or isinstance(element, music21.chord.Chord):
            if element.activeSite.activeSite.activeSite == score.parts[1]:
                if not already_reset:
                    print("reset index")
                    current_dynamic_index = 0
                    already_reset = True
                # update the current_dynamic_index
                element_offset = element.getOffsetInHierarchy(score)
                try:
                    if element_offset >= right_hand_dynamics[current_dynamic_index+1][1]:
                        print("incr index")
                        current_dynamic_index += 1  
                except:
                    #nothing
                    print("nothing")
            element.articulations.clear()
            if element.duration.quarterLength == Fraction(1,3):
                # if it's the right hand accompaniment
                voice_highlighting = 0.4
            elif element.activeSite.activeSite.activeSite == score.parts[0]: # if it's the right hand melody, highlight
            
                voice_highlighting = 0.9
            else: # it's the left hand chords
                voice_highlighting = 0.6
            try:
                element.volume.velocity = right_hand_dynamics[current_dynamic_index][0] * voice_highlighting
            except:
                #print("l o r r : ", element.activeSite.activeSite == score.parts[0])
                #print("index:", current_dynamic_index, " rhds:", len(right_hand_dynamics))
                element.volume.velocity = element.volume.getDynamicContext().volumeScalar * voice_highlighting
                print("set at ", element.volume.velocity)
            #if isinstance(element.activeSite.activeSite, music21.stream.Measure) and element.activeSite.activeSite.measureNumber in [6,7]:
                #print("note:", element.duration, element.volume.velocity, element.volume.getRealized())
    for e in to_remove:
        e.activeSite.remove(e)

def set_default_velocity(score):
    iterate_over_dynamics(score)
    for element in score.recurse():
        if isinstance(element, music21.note.Note):
            is_left_hand(element)
            if element.volume.velocity is None: 
                print(f"found none note: duration={element.duration.quarterLength}")
                # default volume from music21
                element.volume.velocity = DEFAULT_VELOCITY
            else: 
                print(f"not none: {element.volume.velocity}, duration = {element.duration.quarterLength}")

def merge_hands(score: music21.stream.Score):
    new_left = music21.stream.Part()
    right_hand = score.parts[0]
    left_hand = score.parts[1]
    #for element in left_hand.flat.notes:
    #    print("offset", element.offset)
    #    right_hand.insert(element.offset, element)
    #left_hand.activeSite.remove(left_hand)
    # Create a new Score object with the merged part

    for n in left_hand.getElementsByClass("Measure"):
        new_left.insert(n.offset, n)
    score.remove(left_hand)
    score.remove(right_hand)
    score.insert(0, new_left)
    return score

def merge_hands_pm(midi_path):
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    left_hand = midi_data.instruments[1]
    right_hand = midi_data.instruments[0]
    right_hand.notes.extend(left_hand.notes)
    right_hand.control_changes.extend(left_hand.control_changes)
    midi_data.instruments.remove(left_hand)
    midi_data.write(midi_path)


def add_pedal(midi_path, save_path):
    midi_data = pretty_midi.PrettyMIDI(midi_path)
    left_hand = midi_data.instruments[1]
    right_hand = midi_data.instruments[0]
    pedal_changes = []
    for note in left_hand.notes:
        if note.start in pedal_changes:
            continue
        pedal_changes.append(note.start)
    
    sustain_pedal_start = pretty_midi.ControlChange(number=64, value=100, time=0) # start with pedal
    left_hand.control_changes.append(sustain_pedal_start)
    for t in pedal_changes:
        add_at(0, t+0.01, left_hand, right_hand)
        add_at(100, t+0.02, left_hand, right_hand)
    midi_data.write(save_path)

def add_at(value, time, inst1, inst2):
    for inst in [inst1, inst2]:
        inst.control_changes.append(pretty_midi.ControlChange(number=64, value=value, time=time))



def offset_all_velocities(score, offset):
    for element in score.recurse():
        if isinstance(element, music21.note.Note):
            if element.volume.velocity is not None:
                element.volume.velocity += offset


# Main function of the assignment, takes an unperformed MIDI or
#  XML path and outputs a performed midi
def interpret(midi_path, xml_path):
    """
    Main idea:
        Velocity changes can be done "in-place".
        Rhythmic/Tempo changes are more complex since accelerating/slowing down will affect all
        the onsets of all the following notes. Therefore we need some datastructure to allow to
        accumulate changes that will be all compiled/applied in the end at the same time.
        The structure would allow in-place modifications of rhythm.
        Operations need to be reversible and commutative. Some operation should always be able
        to revert its effects, even when another operation is happening conccurently, in a way
        such that the values in the end are as if only the second operation was being applied.
        (for example, shart 8th note scale modifications and slow crescendo at the same time,
        the crescendo shouldn't be perturbed by the small expressiveness).
        An idea could be to use log/exp/multiplicative stuff. so that we do additions in the
        exp realm or something, and that's commutative and satisfies what we need. idk.
        We can have 2 concepts, an expressive timing could be:
            local: for example, the 8th note being rushed a bit or coming too late, without affecting the rest
            global: for example, slowing down at the end of a phrase. This should affect all the score (displace everything by a bit)
    """
    midi_score: music21.stream.Score = music21.converter.parse(midi_path)
    xml_score: music21.stream.Score = music21.converter.parse(xml_path)

    # Let's say I have a note n of onset o, duration d.
    # If I want to make it f times as long (in other words, stretch the time by f between o and o+d):
    # for all notes that start and finish before o:
    #     -> this changes nothing for them
    # for all notes that start before o but finish after o:
    #     -> this changes only their duration: we must add the part of their duration that's at the same time as n times f
    # for all notes (o', d') that start between o and o+d, we must:
    #     -> add (o' - o) * f to their onset
    #     -> add the part of their duration that's at the same time as n times f
    # for all notes (o', d') that start after o:
    #     -> just add d * f to their onset

    timing_modifier = []

    #set_default_velocity(xml_score)
    overwrite_velocities(xml_score) 

    #idea_12(xml_score)

    idea_4(xml_score)

    #idea_13()
                    
    #offset_all_velocities(xml_score, -20)
    #xml_score = merge_hands(xml_score)

    performed_score = xml_score

    # we will write midi in run_transfer
    save_midi = './result.mid'
    pedal_path = './with_pedal.mid'
    performed_score.write("midi", save_midi)
    add_pedal(save_midi, pedal_path)
    merge_hands_pm(pedal_path)

    return performed_score
