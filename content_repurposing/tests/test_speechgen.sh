#!/bin/bash
# Quick test — SpeechGen.io TTS API (curl)
# Run from the project root: bash tests/test_speechgen.sh
# Output saved to: tests/output/test_speechgen.mp3

TOKEN="8f56bc97-2054-4a1b-9c14-8817eb5adf7e"
EMAIL="florian.shllaku@gmail.com"

curl -X POST "https://speechgen.io/index.php?r=api/text" \
  -d "token=$TOKEN" \
  -d "email=$EMAIL" \
  -d "voice=Ada AL" \
  -d "text=Sam Altman parashikoi që AI do krijonte kompaninë e parë miliardëshe me një person — dhe kjo tashmë po ndodh. Një sipërmarrës ndërtoi një biznes që gjeneron qindra miliona vetëm me ndihmën e AI, pa ekip të madh apo investitorë. Pyetja nuk është më nëse AI po ndryshon lojën, por nëse po vepron ndërkohë që të tjerët vetëm po flasin." \
  -d "format=mp3" \
  -d "speed=1" \
  -d "sample_rate=24000" \
  -d "bitrate=192" \
  -d "channels=2" \
  -d "style=newscast"
