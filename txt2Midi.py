import ssl
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from midiutil import MIDIFile
import pandas as pd
import syllapy
import random



#ENTER PATH OF TEXT FILE (just name if it is in same folder as this program)
TEXT_PATH = "Great_Gatsby.txt"

#Enter number of lines you want to analyze, it takes awhile to do whole file (dependent on hardware)
NUM_LINES = 20

def sentence_syllables(sentence):
    word_list = sentence.split()
    syllable_list = []
    for w in word_list:
        syllable_list.append(syllapy.count(w))
    
    return syllable_list


def make_duration(sent_len, percentiles):
    duration = 0
    if sent_len > percentiles[0.75]:
        duration = 4
    elif sent_len > percentiles[0.50]:
        duration = 3
    elif sent_len > percentiles[.25]:
        duration = 2
    else:
        duration = 1
    
    return duration


def make_volume(pos_sent):
    vol = 60    #this is the quietest a note will be
    if pos_sent < 0.1:
        return vol
    else:
        vol_increase = 67 * pos_sent
        return int(vol + vol_increase)

def make_first_chord(sent_dict, root):
    
    IN_2 = 1
    MAJ_2 = 2
    MIN_3 = 3
    MAJ_3 = 4
    PERF_4 = 5
    TRITONE = 6
    PERF_5 = 7
    MAJ_6 = 9
    DOM_7 = 10
    MAJ_7 = 11

    new_chord = [root]
    compound_sum = 0

    for d in sent_dict:
        
        comp = d["compound"]

        compound_sum += comp

    if compound_sum > 0:
        new_chord += [root + MAJ_3]
    
    else:
        new_chord += [root + MIN_3]


    new_chord += [root + random.choice([PERF_4, PERF_5])]

    return new_chord, compound_sum



def make_chord(sent_dict, last_comp, last_root):
    new_chord = []
    root = last_root
    shift = 0
    maj_intervals = [2, 4, 5, 7]
    min_intervals = [1, 3, 5, 8]
    
    MIN_2 = 1
    MAJ_2 = 2
    MIN_3 = 3
    MAJ_3 = 4
    PERF_4 = 5
    TRITONE = 6
    PERF_5 = 7
    MAJ_6 = 9
    DOM_7 = 10
    MAJ_7 = 11

    neg = sent_dict["neg"]
    neu = sent_dict["neu"]
    pos = sent_dict["pos"]
    comp = sent_dict["compound"]

    #overall sentiment difference between this note and last note
    comp_dif = comp - last_comp

    #choose root note
    if abs(comp_dif) < .09:
        root_note = last_root
        new_chord += [root]
        #leave root note for next chord

    #######ROOT
    
    elif comp > 0 and comp_dif > 0: #if the note is positive and more positive than last note, move up major interval
        root = last_root + random.choice(maj_intervals)
        new_chord += [root]

    
    elif comp > 0 and comp_dif < 0: #note is positive but less positive than previous
        root = last_root + (-1 * random.choice(maj_intervals))
        new_chord += [root]

    elif comp < 0 and comp_dif < 0: #note is overall neg and more neg than previous
        root = last_root + random.choice(min_intervals)
        new_chord += [root]

    elif comp < 0 and comp_dif > 0: #note is overall neg and less neg than previous
        root = last_root + (-1 * random.choice(min_intervals))
        new_chord += [root]

    else:
        root = last_root + random.choice([PERF_4, PERF_5])
        new_chord += [root]

    

    #######2nd Note
    #if its a pretty neutral sentence, the next note is just the 3rd
    if neu > .55 and comp > 0:
        next_note = root + MAJ_3
        new_chord += [next_note]

    elif neu > .55 and comp < 0:
        next_note = root + MIN_3
        new_chord += [next_note]

    #if its not neutral then make dissonant chord
    elif neu < .55 and comp > 0:
        next_note = root + MAJ_2
        new_chord += [next_note]

    elif neu < .55 and comp < 0:
        next_note = root + MIN_2
        new_chord += [next_note]


    #######3rd Note
    #if the note is really happy, add MAJ_5 and MAJ_7
    if comp > .5 and comp_dif > 0:
        next_note = root + PERF_5
        new_chord += [next_note]

        next_note = root + MAJ_7
        new_chord += [next_note]
    
    #if the note is really sad, add MAJ_5 and MIN_7
    elif comp < -.5 and comp_dif < 0:
        next_note = root + PERF_5
        new_chord += [next_note]

        next_note = root + DOM_7
        new_chord += [next_note]

    elif comp > 0:
        next_note = root + random.choice([PERF_5, MAJ_7])
        new_chord += [next_note]

    elif comp < 0:
        next_note = root + random.choice([PERF_5, DOM_7])
        new_chord += [next_note]

    else:
        next_note = root + PERF_5
        new_chord += [next_note]


    

    return new_chord


def make_melody(sent_dict, chord, duration, midi, melody_track, cur_time):
    
    melody_list = []
    maj_intervals = [2, 4, 5, 7, 11]
    min_intervals = [1, 3, 5, 8]
    
    MIN_2 = 1
    MAJ_2 = 2
    MIN_3 = 3
    MAJ_3 = 4
    PERF_4 = 5
    TRITONE = 6
    PERF_5 = 7
    MAJ_6 = 9
    DOM_7 = 10
    MAJ_7 = 11

    syllables = sent_dict["Syllables"]

    
    first_interval = chord[1] - chord[0]
    

    ROOT = chord[0]

    vol = 105

    #TWO_BARS = 16

    note_dur = .25

    if duration <= 1:
        return melody_list
    elif duration == 4:
        solo_end = cur_time + 4
        if first_interval == MAJ_3:
            solo_intervals = maj_intervals
        elif first_interval == MIN_3:
            solo_intervals = min_intervals

        counter = 0
        solo_time = 0
        first_note = ROOT + random.choice(solo_intervals)
        melody_list.append([melody_track, 0, first_note, cur_time, note_dur, vol])
        cur_time += note_dur
        solo_time += note_dur
        last_note = first_note
        while solo_time < duration:
            if counter == len(syllables):
                break
            syl_count = syllables[counter]
            note_index = syl_count % len(solo_intervals)
            next_note = last_note + (random.choice([-1,0]) * solo_intervals[note_index])
            next_dur = syl_count * note_dur
            vol = vol + (random.choice([-1,0]) * syl_count)

            if vol > 126:
                vol = 105
            elif vol < 30:
                vol = 95
    
            if cur_time + next_dur > solo_end:
                
                break
            melody_list.append([melody_track, 0, next_note, cur_time, next_dur, vol])
            solo_time += next_dur
            cur_time += next_dur
            counter += 1

    
    
    return melody_list



def make_bass(chord, cur_time, chord_dur, melody_list, BASS_TRACK):
    #dont forget, bass notes want to go down at least an octave
    bass_chord = []

    bass_notes = []
    vol = 90
    MIN_2 = 1
    MAJ_2 = 2
    MIN_3 = 3
    MAJ_3 = 4
    
    for note in chord:
        bass_chord += [note - 12]
    
    root = bass_chord[0]

    first_interval = bass_chord[1] - bass_chord[0]

    notes = len(bass_chord)
    dur = 1
    
    
    if chord_dur == 1 and notes == 3 and first_interval == MAJ_3:
        bass_root = root - 3
        bass_root_list = [BASS_TRACK, 0, bass_root, cur_time, dur, vol]
        bass_notes.append(bass_root_list)

        return bass_notes
    
    elif chord_dur == 1:
        bass_root_list = [BASS_TRACK, 0, root, cur_time, dur, vol]
        bass_notes.append(bass_root_list)

        return bass_notes
    
    elif chord_dur == 2:
        bass_root = root
        bass_root_list = [BASS_TRACK, 0, bass_root, cur_time, dur, vol]
        bass_notes.append(bass_root_list)
        
        cur_time += dur

        bass_note = random.choice(bass_chord[1:])    #any note but root
        bass_note_list = [BASS_TRACK, 0, bass_note, cur_time, dur, vol]
        bass_notes.append(bass_note_list)

    elif chord_dur == 3: #bass solo
        total_dur = 0
        bass_root = random.choice([root, root - 3])
        dur_list = [.125, .25, .5]
        dur = random.choice(dur_list)
        bass_root_list = [BASS_TRACK, 0, bass_root, cur_time, dur, vol]
        bass_notes.append(bass_root_list)

        total_dur += dur
        cur_time += dur
        last_note = bass_root

        while total_dur < 3:
            dur_list = [.125, .25, .5]
            dur = random.choice(dur_list)
            
            bass_note = random.choice([root, root - 3,root + 7])
            bass_note_list = [BASS_TRACK, 0, bass_note, cur_time, dur, vol]
            while bass_note == last_note:
                bass_note = random.choice([root, root - 3, root + 7, bass_chord[-1]])
            
            if total_dur + dur > 3:
                dur = 3 - total_dur

            bass_notes.append(bass_note_list)

            total_dur += dur
            cur_time += dur

    else:
        total_dur = 0
        
        while total_dur < chord_dur:
            for note in bass_chord:
                bass_note = note
                dur = 1
                if total_dur < chord_dur:
                    

                    
                    if total_dur + dur > chord_dur:
                        dur = chord_dur - total_dur
                        bass_note_list = [BASS_TRACK, 0, bass_note, cur_time, dur, vol]
                        bass_notes.append(bass_note_list)

                        total_dur += dur
                        cur_time += dur

                        
                    
                    bass_note_list = [BASS_TRACK, 0, bass_note, cur_time, dur, vol]
                    bass_notes.append(bass_note_list)

                    total_dur += dur
                    cur_time += dur

            


    return bass_notes
        




# MIDI note number for C Maj scale
C_MAJ_SCALE  = [60, 62, 64, 65, 67, 69, 71, 72]


# Download the VADER lexicon if not already available and punkt_tab
nltk.download('vader_lexicon')

nltk.download('punkt_tab')



# Initialize the sentiment analyzer from nltk
analyzer = SentimentIntensityAnalyzer()

#create empty list to store sentiment results
sentiment_results = []



# Read the text file
with open(TEXT_PATH, 'r') as file:
    text = file.read()

# Tokenize the text into sentences
book = nltk.sent_tokenize(text)

# Create a pandas DataFrame with the length of each sentence
df = pd.DataFrame({'sentence': book})
df['length'] = df['sentence'].apply(len)

# Calculate the average length of the sentences
average_length = df['length'].mean()

# Calculate the 25th, 50th, and 75th percentiles of sentence length
percentiles = df['length'].quantile([0.25, 0.50, 0.75])


#loop through sentences and analyze them
for sentence in book[:NUM_LINES]:
    sentiment = analyzer.polarity_scores(sentence)
    sentiment["Length"] = len(sentence)
    sentiment["Syllables"] = sentence_syllables(sentence)
    sentiment_results.append(sentiment)


#sentiment_results now equals a list of dictionaries, each dictionary relates to a midi note

#midi stuff
track    = 0
channel  = 0    
time     = 0    # In beats
duration = 1    # In beats
tempo    = 105   # In BPM
volume   = 100  # 0-127, as per the MIDI standard

MyMIDI = MIDIFile(3)  # One track, defaults to format 1 (tempo track is created
                      # automatically)

MyMIDI.addTempo(track, time, tempo)

bass_name = "BASS"
BASS_TRACK = 0
MyMIDI.addTrackName(BASS_TRACK, 0, bass_name)   #track 0 is for bass and it starts at zero
MyMIDI.addNote(BASS_TRACK, channel, 60, 0, 1, volume)

chords_name = "Piano_Chords"
CHORDS_TRACK = 1
MyMIDI.addTrackName(CHORDS_TRACK, 0, chords_name)   #track 1 is for piano chords and it starts at zero

melody_name = "Piano_Melody"
MELODY_TRACK = 2
MyMIDI.addTrackName(MELODY_TRACK, 0, melody_name)   #track 2 is for piano melody and it starts at zero


FIRST_ROOT = 60

FIRST_CHORD, last_note_compound = make_first_chord(sentiment_results, FIRST_ROOT)


for n in FIRST_CHORD:
    MyMIDI.addNote(CHORDS_TRACK, channel, n, 0, 1, volume)
    

last_note_pitch = 60

#for keeping track of "time"
master_time = 1

#turn sentiment_results into midi notes
for sent_dict in sentiment_results:
    
    #determine note time
    time = master_time

    #determine duration
    sent_len = sent_dict["Length"]
    duration = make_duration(sent_len, percentiles)
    
    
    #determine volume
    sent_pos = sent_dict["pos"]
    vol = make_volume(sent_pos)
    

    #determine chord
    new_chord = make_chord(sent_dict, last_note_compound, last_note_pitch)
    

    
    #add notes from chord
    for n in new_chord:
        MyMIDI.addNote(CHORDS_TRACK, channel, n, time, duration, vol)


    #create melody and add it to midi thing
    melody_list = make_melody(sent_dict, new_chord, duration, MyMIDI, MELODY_TRACK, master_time)

    if melody_list:
        for note_list in melody_list:
            
            MyMIDI.addNote(*note_list)

    #create bass line
    bass_list = make_bass(new_chord, master_time, duration, melody_list, BASS_TRACK)
    
    if bass_list:
        for note_list in bass_list:
            
            MyMIDI.addNote(*note_list)

    #move time for next note
    master_time += duration

    #track last compound score and the last note
    last_note_compound = sent_dict["compound"]
    last_note_root = new_chord[0]



with open("my_song.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)





