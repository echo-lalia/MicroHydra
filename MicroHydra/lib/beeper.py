from machine import I2S, Pin
import math

_SCK_PIN = const(41)
_WS_PIN = const(43)
_SD_PIN = const(42)
_I2S_ID = const(1)
_BUFFER_LENGTH_IN_BYTES = const(2048)
_SAMPLE_SIZE_IN_BITS = const(16)
_FORMAT = I2S.STEREO
_SAMPLE_RATE_IN_HZ = const(16000)

volume_map = {0:1,1:4,2:10,3:16,4:20,5:28,6:36,7:50,8:60,9:80,10:127}
tone_map = {
"C3": 131,
"CS3": 139,
"D3": 147,
"DS3": 156,
"E3": 165,
"F3": 175,
"FS3": 185,
"G3": 196,
"GS3": 208,
"A3": 220,
"AS3": 233,
"B3": 247,
"C4": 262,
"CS4": 277,
"D4": 294,
"DS4": 311,
"E4": 330,
"F4": 349,
"FS4": 370,
"G4": 392,
"GS4": 415,
"A4": 440,
"AS4": 466,
"B4": 494,
"C5": 523,
"CS5": 554,
"D5": 587,
"DS5": 622,
"E5": 659,
"F5": 698,
"FS5": 740,
"G5": 784,
"GS5": 831,
"A5": 880,
"AS5": 932,
"B5": 988
}

class Beeper:
    def __init__(self, buf_size=4000):
        
        self._output = I2S(            
            _I2S_ID,
            sck=Pin(_SCK_PIN),
            ws=Pin(_WS_PIN),
            sd=Pin(_SD_PIN),
            mode=I2S.TX,
            bits=_SAMPLE_SIZE_IN_BITS,
            format=_FORMAT,
            rate=_SAMPLE_RATE_IN_HZ,
            ibuf=_BUFFER_LENGTH_IN_BYTES)
        
        self._current_notes = []

        self.buf_size = buf_size
        self._buf = bytearray(buf_size)
        self._mv = memoryview(self._buf)
        
        
    def __del__(self):
        self._output.deinit()
        
        
    #@micropython.viper #viper HATES my esp32-s3 :(
    # it works when uncompiled. But compiled, it deep-fries all the audio. 
    def gen_square_wave(self, frequency:int, time_ms:int, high_sample:int) -> int:
        """
        Rough micropython viper method for generating a square wave. Wave it put in self._buf,
        and returns the end index of the gennerated wave in _buf
        """

        
        # 2 bytes per sample
        samples_per_segment = 16000 // (frequency * 2)
        
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency * 2)
        samples_per_segment_low = samples_per_segment + (samples_per_segment_remainder // frequency)
        
        total_samples = 16 * time_ms
        
        #total_repetitions = total_samples // (samples_per_segment * 2) 
        number_of_bytes = total_samples * 2
        #this is needed in case our samples per segment overshoots our actual bytearray size
        byte_safe_ending = number_of_bytes - (samples_per_segment * 32)
        
        written_bytes = 0
        high_sample_counter = 0
        low_sample_counter = 0
        while written_bytes < byte_safe_ending: #write samples until total samples written
            
            #write high samples
            while high_sample_counter < samples_per_segment:
                # 16 bit samples but only 8 bits are read. Feels silly but I think we have to double these up.
                self._buf[written_bytes] = high_sample
                written_bytes += 1
                self._buf[written_bytes] = high_sample 
                written_bytes += 1
                high_sample_counter += 1
            
            #write low samples
            while low_sample_counter < samples_per_segment_low:
                self._buf[written_bytes] = 0x00
                written_bytes += 1
                self._buf[written_bytes] = 0x00
                written_bytes += 1
                low_sample_counter += 1
            
            #reset samples counters
            high_sample_counter = 0
            low_sample_counter = 0
        
        return written_bytes
    
    
    
    #@micropython.viper
    def double_square_wave(self, frequency1:int, frequency2:int, time_ms:int, high_sample:int) -> int:
        """
        This is the same as self.gen_square_wave, except it has been refactored to play two frequencies together.
        """
        
        # 2 bytes per sample
        samples_per_segment1 = 16000 // (frequency1 * 2)
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency1 * 2)
        samples_per_segment_low1 = samples_per_segment1 + (samples_per_segment_remainder // frequency1)
        
        
        samples_per_segment2 = 16000 // (frequency2 * 2)
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency2 * 2)
        samples_per_segment_low2 = samples_per_segment2 + (samples_per_segment_remainder // frequency2)
        
        total_samples = 16 * time_ms
        number_of_bytes = total_samples * 2
        
        #this is needed in case our samples per segment overshoots our actual bytearray size
        byte_safe_ending = number_of_bytes - (samples_per_segment1 * 32)
        
        
        
        written_bytes = 0
        high_sample_counter = 0
        low_sample_counter = 0
        high_sample1 = True 
        
        high_sample_counter2 = 0
        low_sample_counter2 = 0
        high_sample2 = True
        while written_bytes < byte_safe_ending: #write samples until total samples written
            

            this_sample = 0
            #calc sample1
            if high_sample1:
                this_sample += high_sample // 2
                high_sample_counter += 1
                if high_sample_counter >= samples_per_segment1:
                    high_sample1 = False
                    high_sample_counter = 0
            else: #low_sample1
                low_sample_counter += 1
                if low_sample_counter >= samples_per_segment_low1:
                    low_sample_counter = 0
                    high_sample1 = True
               
            #calc sample2
            if high_sample2:
                this_sample += high_sample // 2
                high_sample_counter2 += 1
                if high_sample_counter2 >= samples_per_segment2:
                    high_sample2 = False
                    high_sample_counter2 = 0
            else: # low sample2
                low_sample_counter2 += 1
                if low_sample_counter2 >= samples_per_segment_low2:
                    low_sample_counter2 = 0
                    high_sample2 = True
            
            self._buf[written_bytes] = this_sample
            written_bytes += 1
            self._buf[written_bytes] = this_sample
            written_bytes += 1

            

        
        return written_bytes

    #@micropython.viper
    def triple_square_wave(self, frequency1:int, frequency2:int, frequency3:int, time_ms:int, high_sample:int) -> int:
        """
        This is the same as self.gen_square_wave/self.double_square_wave,
        except it has been refactored to play three frequencies together.
        """
        # 2 bytes per sample
        samples_per_segment1 = 16000 // (frequency1 * 3)
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency1 * 2)
        samples_per_segment_low1 = samples_per_segment1 + (samples_per_segment_remainder // frequency1)
        
        samples_per_segment2 = 16000 // (frequency2 * 3)
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency2 * 2)
        samples_per_segment_low2 = samples_per_segment2 + (samples_per_segment_remainder // frequency2)
        
        samples_per_segment3 = 16000 // (frequency3 * 3)
        #this is for helping to distinguish notes from eachother who would get garbled together thanks to int division
        samples_per_segment_remainder = 16000 % (frequency3 * 2)
        samples_per_segment_low3 = samples_per_segment3 + (samples_per_segment_remainder // frequency3)
        
        total_samples = 16 * time_ms
        number_of_bytes = total_samples * 2
        #this is needed in case our samples per segment overshoots our actual bytearray size
        byte_safe_ending = number_of_bytes - (samples_per_segment1 * 32)
        
        written_bytes = 0
        high_sample_counter = 0
        low_sample_counter = 0
        high_sample1 = True 
        
        high_sample_counter2 = 0
        low_sample_counter2 = 0
        high_sample2 = True
        
        high_sample_counter3 = 0
        low_sample_counter3 = 0
        high_sample3 = True
        while written_bytes < byte_safe_ending: #write samples until total samples written
            
            this_sample = 0
            #calc sample1
            if high_sample1:
                this_sample += high_sample // 3
                high_sample_counter += 1
                if high_sample_counter >= samples_per_segment1:
                    high_sample1 = False
                    high_sample_counter = 0
            else: #low_sample1
                low_sample_counter += 1
                if low_sample_counter >= samples_per_segment_low1:
                    low_sample_counter = 0
                    high_sample1 = True
               
            #calc sample2
            if high_sample2:
                this_sample += high_sample // 3
                high_sample_counter2 += 1
                if high_sample_counter2 >= samples_per_segment2:
                    high_sample2 = False
                    high_sample_counter2 = 0
            else: # low sample2
                low_sample_counter2 += 1
                if low_sample_counter2 >= samples_per_segment_low2:
                    low_sample_counter2 = 0
                    high_sample2 = True
            
            #calc sample3
            if high_sample3:
                this_sample += high_sample // 3
                high_sample_counter3 += 1
                if high_sample_counter3 >= samples_per_segment3:
                    high_sample3 = False
                    high_sample_counter3 = 0
            else: # low sample3
                low_sample_counter3 += 1
                if low_sample_counter3 >= samples_per_segment_low3:
                    low_sample_counter3 = 0
                    high_sample3 = True
            
            self._buf[written_bytes] = this_sample
            written_bytes += 1
            self._buf[written_bytes] = this_sample
            written_bytes += 1

        return written_bytes
    
    
    
    def play_chorus(self, note, time_ms, volume):
        """
        Play a single note in multiple octaves. This method is probably not as useful as the regular self.play method.
        """
        freq = tone_map[note]
        
        #find note2
        note_octave = int(note[-1])
        note_without_octave = note[:-1]
        note2 = note_without_octave + str(note_octave - 1)
        if note2 in tone_map.keys():
            freq2 = tone_map[note2]
        else:
            freq2 = freq - 1

        high_sample = volume_map[volume]

        while time_ms * 32 > self.buf_size:
            time_ms -= self.buf_size // 32
            written_samples = self.double_square_wave(freq, freq2, self.buf_size // 32, high_sample)
            self._output.write(self._mv[0:written_samples])

        written_samples = self.double_square_wave(freq, freq2, time_ms, high_sample)
        self._output.write(self._mv[0:written_samples])
        
        
    def play_freq(self, freq, time_ms, volume):
        """Simply play the given frequency"""
        high_sample = volume_map[volume]

        while time_ms * 32 > self.buf_size:
            time_ms -= self.buf_size // 32
            written_samples = self.gen_square_wave(freq, self.buf_size // 32, high_sample)
            self._output.write(self._mv[0:written_samples])

        written_samples = self.gen_square_wave(freq, time_ms, high_sample)
        self._output.write(self._mv[0:written_samples])
        
        
    def play_double(self, freq, freq2, time_ms, volume):
        """Simply play the two given frequencies"""
        high_sample = volume_map[volume]

        while time_ms * 32 > self.buf_size:
            time_ms -= self.buf_size // 32
            written_samples = self.double_square_wave(freq, freq2, self.buf_size // 32, high_sample)
            self._output.write(self._mv[0:written_samples])

        written_samples = self.double_square_wave(freq, freq2, time_ms, high_sample)
        self._output.write(self._mv[0:written_samples])
    
    
    def play_triple(self, freq, freq2, freq3, time_ms, volume):
        """Simply play the three given frequencies"""
        high_sample = volume_map[volume]

        while time_ms * 32 > self.buf_size:
            time_ms -= self.buf_size // 32
            written_samples = self.triple_square_wave(freq, freq2, freq3, self.buf_size // 32, high_sample)
            self._output.write(self._mv[0:written_samples])

        written_samples = self.triple_square_wave(freq, freq2, freq3, time_ms, high_sample)
        self._output.write(self._mv[0:written_samples])
    
    
    
    def play(self, notes, time_ms=100, volume=4):
        """
        This is the main outward-facing method of Beeper.
        Use this to play a simple square wave over the SPI speaker.
        
        "notes" can be:
        - a string containing a note's name,
        - a list/tuple containing notes to play.
            If "notes" is a list/tuple, it's entries can be:
            - a string containing a note's name,
            - a tuple of strings of notes names, to be played together (like a chord).
            
        "time_ms" is the time in milliseconds to play each note for.
        If time_ms creates a note longer than Beeper's internal buffer, then each note will
        be played multiple times to achieve the requested length.
        
        "volume" is an integer between 0 and 10.
        """
        high_sample = volume_map[volume]
        
        if type(notes) == str:
            self.play_freq(tone_map[notes], time_ms, volume)
        else:
            for note in notes:
                if type(note) == str:
                    self.play_freq(tone_map[note], time_ms, volume)
                elif len(note) == 1:
                    self.play_freq(tone_map[note[0]], time_ms, volume)
                elif len(note) == 2:
                    self.play_double(tone_map[note[0]],tone_map[note[1]], time_ms, volume)
                else:
                    self.play_triple(tone_map[note[0]],tone_map[note[1]], tone_map[note[2]], time_ms, volume)
    
    
if __name__ == "__main__":
    import time
    beep = Beeper()
    #beep.play_chorus('C4',200,10)
    beep.play((
        ('G3'),
        ('G3','C3'),
        ('G3','C3','E3'),
        ('C3','E3','A3'),
        ('C3','E3','A3'),
        ('C3','E3','A3'),
        ), 300, 5)
    time.sleep(1)
    beep.play((('C4','C5','C3'),('B3','B3','B3'),('A3','A3','A3'),('A3','A3','A3'),('B3','B3','B3')),400,4)
    



