import music21
import src.data as data
import math
from fractions import Fraction

def is_rh_accompaniement(element: music21.note.Note):
    d : music21.Duration = element.duration
    return d.quarterLength == Fraction(1,3)

"""
Add an ascending bell curve shape to velocity and speed for accommpaniment right-hand 8th notes 
"""
def idea_4(element: music21.note.Note, score: music21.stream.Score):
    pos_in_motif = (element.offset * 3) % 6
    bell_curve = (-pos_in_motif**2 + 5*pos_in_motif)
    v = element.volume.velocity
    if v is None: 
        v = 28
    v -= 10 # I do this because the accompaniment seems to loud on the unperformed midi
    velocity_increase = 0.8*bell_curve # the 6 8th note motif's velocities form a clear bell curve in many recordings
    element.volume.velocity = v + velocity_increase

    #t = get_current_tempo(score, element.offset)
    base_tempo = 120
    t2 = base_tempo + 2.5*bell_curve
    if (element.offset * 3) % 24 == 23: # if we're in the beat just before 
        t2 = base_tempo - 15 # I do this to delay each beat after the last of th 6 8th note, as can be clearly heard in Kociuban's performance
        # But actually, it's not each beat, it's just before the melody. If we can detect the melody, we can do it automatically
    
    # setting the new tempo at that offset
    m = music21.tempo.MetronomeMark(number=t2)
    m.offset = element.offset
    print(f"inserting tempo change {m} ({t2})")
    score.insert(element.offset, m)

def get_current_tempo(score, offset):
    tempo_closest_to_offset = 120
    for event in score.flat.getElementsByClass(music21.tempo.MetronomeMark):
        if event.offset <= offset:
            tempo_closest_to_offset = event.number
        else:
            return tempo_closest_to_offset

"""
Main function of the assignment, takes an unperformed MIDI or XML path and outputs a performed midi
"""
def interpret(unperformed_path):
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
    unperformed_score : music21.stream.Score = music21.converter.parse(unperformed_path)

    """
    Let's say I have a note n of onset o, duration d.
    If I want to make it f times as long (in other words, stretch the time by f between o and o+d):
    for all notes that start and finish before o:
        -> this changes nothing for them
    for all notes that start before o but finish after o:
        -> this changes only their duration: we must add the part of their duration that's at the same time as n times f
    for all notes (o', d') that start between o and o+d, we must:
        -> add (o' - o) * f to their onset
        -> add the part of their duration that's at the same time as n times f
    for all notes (o', d') that start after o:
        -> just add d * f to their onset
    """
    timing_modifier = []
    
    for part in unperformed_score.parts:
        for element in part.flat.notes:
            if isinstance(element, music21.note.Note) and is_rh_accompaniement(element):
                idea_4(element, unperformed_score)

    performed_score = unperformed_score
    performed_score.write("midi", './result.mid')

    return performed_score