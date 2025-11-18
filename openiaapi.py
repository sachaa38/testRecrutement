from openai import OpenAI
import requests
from pathlib import Path

client = OpenAI(api_key="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")


def getCompletion(prompt, system_prompt= "", messages=[]):
  if system_prompt != "" and len(messages) == 0:
    messages.append({"role":"system", "content": system_prompt})

  messages.append({"role": "user", "content": prompt})

  try:

    response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages
    )

    text = response.choices[0].message.content
    messages.append({"role": "assistant", "content": text})
    return text
  except Exception as e:
    print("OpenIA Execption :" + str(e))
  
  return None

def generateImage(prompt, filename = "") :

  result = client.images.generate(
      model="dall-e-3",
      prompt=prompt,
      size="1024x1024"
)

  imageUrl = result.data[0].url

  if filename != "": 
    image_data = requests.get(imageUrl).content
    with open(filename, 'wb') as file:
      file.write(image_data)

  return imageUrl

def generateAudio(prompt, filename):
  
  response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="alloy",
    input=prompt
  )
  response.write_to_file(filename)


if __name__ == "__main__":
  print(getCompletion('Bonjour'))
  # print("Image en cours de création...")
  # print(generateImage("a picture of a great beautiful russia", "russia.png"))
  # print("Image générée !")
  # generateAudio("Bonjour, comment allez vous ?", "speech.mp3")