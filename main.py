import discord
import openai
import time
import os
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from mutagen.mp3 import MP3
import WebServer
r = sr.Recognizer()

openai.api_key = "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"


def vc_required(func):
    async def get_vc(self, msg):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc



class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = {voice.guild.id: voice for voice in self.voice_clients}
        self.playlists = {}

        self.commands = {
            '!conversation': self.start_recording,
            '!stop': self.stop_recording,
            '!end': self.end_conversation,
        }

    async def get_vc(self, message):
        vc = message.author.voice
        if not vc:
            await message.channel.send("You're not in a vc right now")
            return
        connection = self.connections.get(message.guild.id)
        if connection:
            if connection.channel.id == message.author.voice.channel.id:
                return connection

            await connection.move_to(vc.channel)
            return connection
        else:
            vc = await vc.channel.connect()
            self.connections.update({message.guild.id: vc})
            return vc

    async def on_message(self, msg):
        if not msg.content:
            return
        cmd = msg.content.split()[0]
        if cmd in self.commands:
            await self.commands[cmd](msg)

    @vc_required
    async def start_recording(self, msg, vc):
      try:
        vc.start_recording(discord.Sink(), self.finished_callback, msg.channel)

        await msg.channel.send("The conversation has started! Type `!stop` to end the current question.")
      except Exception as e:
        await msg.channel.send("An error has occurred. Likely the bot was already listening to a conversation in this server.")
        await msg.channel.send("Exception: "+str(e))
        return


    @vc_required
    async def end_conversation(self, msg, vc):
        vc.stop_recording()
        global bobbio
        bobbio = True
        #tts = gTTS("Thanks for chatting with me. Good bye.")
        #tts.save('goodbye.mp3')

        bob.play(discord.FFmpegOpusAudio(source="bot_audio_files/goodbye.mp3"), after=lambda e: print('done', e))
        #bobs_audio = MP3("bot_audio_files/goodbye.mp3")
        #audio_length = bobs_audio.info.length+1
        #print(audio_length)


        time.sleep(4.072)
        await vc.disconnect()
        await msg.channel.send("The conversation has ended.")

    @vc_required
    async def stop_recording(self, msg, vc):
        global bob
        global tom
        global bobbio
        bob = vc
        tom = msg
        bobbio = False
        vc.stop_recording()


    async def finished_callback(self, sink, channel, *args):


        if bobbio:
            return
        
        try:
          recorded_users = [
              f" <@{str(user_id)}> ({os.path.split(audio.file)[1]}) "
              for user_id, audio in sink.audio_data.items()
          ]
          s=recorded_users[0]
          audio = s[s.find('(')+1:s.find(')')]
          print(audio)
          stereo_audio = AudioSegment.from_file(audio,format="wav")
          mono_audios = stereo_audio.split_to_mono()
          mono_audios[0].export(audio,format="wav")

        except Exception as e:
          await tom.channel.send("An error has occurred. Likely you are muted or you stopped the bot before it could hear you.")
          await channel.send("Exception: "+str(e))
          return

        try:

          with sr.WavFile(audio) as source:
              audio = r.record(source)

          text = r.recognize_google(audio)
        except Exception as e:
          await channel.send("An error has occurred. Likely the bot was unable to understand what you said and it crashed.")
          await channel.send("Exception: "+str(e))
          return
    


        try:
            await channel.send("You said: " + str(text))
            os.remove(s[s.find('(')+1:s.find(')')])
        except Exception as e:
            await channel.send("Exception: "+str(e))
            return
        
        question = text

        response = openai.Completion.create(
        engine="babbage-instruct-beta", #curie-instruct-beta-v2 is better if it's not too expensive
        prompt=f"The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n Human: {question} \n AI: ",
        max_tokens=80,
        temperature=0,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=0,
        stop=["Human:"]
        )
        response=response.choices[0].text.replace('\n','')

        tts = gTTS(response)
        tts.save('bot_audio_files/response.mp3')

        bob.play(discord.FFmpegOpusAudio(source="bot_audio_files/response.mp3"), after=lambda e: print('done', e))

        bobs_audio = MP3("bot_audio_files/response.mp3")
        audio_length = bobs_audio.info.length
        print(audio_length)


        time.sleep(audio_length)
        bob.start_recording(discord.Sink(), self.finished_callback, tom.channel)
        await tom.channel.send("The bot is now listening for your response. Type `!stop` to end the current question or `!end` to end the conversation.")

    

        
        




    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id:
            return
        # Filter out updates other than when we leave a channel we're connected to
        if member.guild.id not in self.connections and (not before.channel and after.channel):
            return

        print("Disconnected")
        del self.connections[member.guild.id]



intents = discord.Intents.default()
client = Client(intents=intents)
WebServer.start()
client.run('OTIzMDM0NTM2Mzk1Mjk2Nzg4.YcKI5g.W0GZKiHpEZLEhzTd-slzPaa2rrE')