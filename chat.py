from openiaapi import *

system_message = "Tu es un enfant de 4 ans qui s'appelle Tommy, tu parles comme tel"
messages = []

while True:
    prompt = input("Vous :")
    print()
    response = getCompletion(prompt, system_message, messages)
    print("Assistant :", response)
    print()