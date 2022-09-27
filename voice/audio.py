import asyncio
import base64
import json

import pyaudio
import websockets
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as SIA

#from config import auth_key

frames_per_buffer = 3200
format = pyaudio.paInt16
channels = 1
rate = 16000
listener = pyaudio.PyAudio()

stream = listener.open(
    format = format,
    channels = channels,
    rate = rate,
    input = True,
    frames_per_buffer = frames_per_buffer
)

auth_key = ''
sentiment_analyzer = SIA()

# AssemblyAI Real-time listener Endpoint
transcription_endpoint = 'wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000'

async def send_receive():
    print('CONNECTING TO ASSEMBLY AI ENDPOINT...')

    async with websockets.connect(
        transcription_endpoint,
        extra_headers = (("Authorization", auth_key),),
        ping_interval = 5,
        ping_timeout = 20
    ) as _ws:

        await asyncio.sleep(0.1)
        print('STARTING SESSION...')
        session_begins = await _ws.recv()
        #print(session_begins)
        print('I AM LISTENING TO YOU...')

        async def send():
            while True:
                try:
                    data = stream.read(frames_per_buffer)
                    data = base64.b64encode(data).decode('utf-8')
                    json_data = json.dumps({'audio_data':str(data)})
                    await _ws.send(json_data)
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    assert False, "Non websockets 4008 error"
                await asyncio.sleep(0.1)
            
            return True
        
        async def receive():
            while True:
                try:
                    result_str = await _ws.recv()
                    senti = sentiment_analyzer.polarity_scores(str(json.loads(result_str)['text']))['compound']*100
                    if len(json.loads(result_str)['text']) > 0:
                        print(f"{senti} | {json.loads(result_str)['text']}", end='\n\n')
                    else:
                        pass
                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    assert False, "Non websockets 4008 error"
        
        send_result, receive_result = await asyncio.gather(send(), receive())

while True:
    try:
        asyncio.run(send_receive())
    except KeyboardInterrupt as e:
        print('KEYBOARD INTERRUPTION... DONE LISTENING.')
        break
