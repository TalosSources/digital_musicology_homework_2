import music21

def idea_4():
    ...

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
    """
    score : music21.stream.Score = music21.converter.parse(unperformed_path)
    for part in score.parts:
        print(part)
        for measure in part:
            print(measure)
            for e in measure:
                print(e)
                if(type(e) == music21.stream.Voice):
                    for f in e:
                        print(f) # TODO : figure out again how to parse this
    return score