import pyaudio
import wave
import time
from pydub import AudioSegment
import io
import os
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
from groq import Groq

client = Groq()

transcription_texts = []

def transcribe_audio(mp3_file, chunk_num):
    mp3_file.seek(0) 
    filename = f"audio_chunk_{chunk_num}.mp3"

    transcription = client.audio.transcriptions.create(
        file=(filename, mp3_file.read()),
        model="distil-whisper-large-v3-en",  
        prompt="Specify context or spelling",  
        response_format="json",  
        language="en",  
        temperature=0.0  
    )

    # Append the transcription text to the global list
    transcription_texts.append(transcription.text)
    print(f"Transcription for chunk {chunk_num}: {transcription.text}")  # Display transcription

# Function to record audio and save as mp3 in 2-second chunks
def record_audio_in_chunks(chunk_duration=2):
    p = pyaudio.PyAudio()

    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    CHUNK = 512  # Reduced chunk size for more frequent reads

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK * 2)  # Increased buffer size

    print(f"Recording audio in {chunk_duration}-second chunks...")

    chunk_num = 0

    try:
        while True:
            frames = []
            for _ in range(0, int(RATE / CHUNK * chunk_duration)):
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)
                except OSError as e:
                    print(f"Audio buffer overflowed: {e}")
                    continue  # Skip this chunk and continue recording

            wave_file = io.BytesIO()
            wf = wave.open(wave_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            wave_file.seek(0)
            audio_segment = AudioSegment.from_wav(wave_file)
            mp3_file = io.BytesIO()
            audio_segment.export(mp3_file, format="mp3")

            chunk_num += 1
            transcription_thread = Thread(target=transcribe_audio, args=(mp3_file, chunk_num))
            transcription_thread.start()

            print(f"Saved and sent chunk {chunk_num} for transcription.")


    except KeyboardInterrupt:
        print("Recording stopped.")

    stream.stop_stream()
    stream.close()
    p.terminate()

# Start recording
record_audio_in_chunks()

final_transcription = " ".join(transcription_texts)
print(f"Final transcription: {final_transcription}")