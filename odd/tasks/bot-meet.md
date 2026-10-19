# bot-meet — asistente flotante para grabar, transcribir y visualizar reuniones

Grabador multi-OS con widget flotante, transcripción local (Whisper) y generación de notas/diagramas vía puerto Analyzer (Ollama local o API por suscripción).

## Specs

- S1: "seria genial que fuera un asistente que este flotando en pantalla y pueda activar rapido para grabar" — widget flotante siempre visible + atajo global para iniciar/detener.
- S2: "Por lo general tengo reuniones en meet (puede ser en otras, team, zoom...)" — captura audio del sistema + micrófono, sin integrarse con cada app.
- S3: "lo idea seria guardar el audio, transcribirlo (whisper?)" — guarda audio y transcribe con Whisper local.
- S4: "que lo pueda dejar en una carpeta respectiva al proyecto" — layout `meetings/<proyecto>/<fecha>/` con audio, transcripción y notas.
- S5: "me gustaria generar diagramas de secuencias, arquitectura o notas visuales para poder entenderlo de manera mas facil" — resumen, decisiones, action items, diagramas Mermaid (secuencia, arquitectura) y mapa mental.
- S6: multi-OS (Windows + macOS). Este PC y un MacBook M5 Air 16 GB.
- S7: transcripción local — RTX 4070 8 GB (CUDA) y M5 (Metal).
- S8: puerto Analyzer con adaptadores — Ollama local o API por suscripción (modelos de la empresa, p. ej. Gemini 3.8 Flash); el usuario decide.
- S9: stack Python + PySide6, entorno con `uv`. Artefactos técnicos en inglés.

## Tasks

- T1 (S1,S2,S6): spike captura audio del sistema en Windows (WASAPI loopback) — route: inline, commit: no.
- T2 (S6): spike captura audio en macOS (ScreenCaptureKit / BlackHole) en la MacBook — route: manual en Mac, commit: no.
- T3 (S9): scaffolding (uv, estructura puertos/adaptadores, layout S4) — route: inline.
- T4 (S1,S2): grabadora — widget flotante + atajo global + sistema + mic — route: inline.
- T5 (S3,S7): puerto Transcriber (faster-whisper CUDA / whisper.cpp-mlx Metal) — route: inline.
- T6 (S4): almacenamiento `meetings/<proyecto>/<fecha>/` — route: con T3/T4.
- T7 (S8): puerto Analyzer (Ollama, Gemini, OpenAI-compatible) — route: inline.
- T8 (S5): generación de notas y diagramas Mermaid — route: inline.
- T9 (S6): empaquetado por OS (instalador Windows + build macOS) — route: último.

## Log

- L1 (pedido original, verbatim): "Hola, quiero empezar un proyecto en esta carpeta. Mi idea es la siguiente. Por lo general tengo reuniones en meet (puede ser en otras, team, zoom...) y me gustaria un programa para poder grabar, seria genial que fuera un asistente que este flotando en pantalla y pueda activar rapido para grabar. Ok, que hacemos con esta grabacion, lo idea seria guardar el audio, transcribirlo (whisper?) y por ultimo que lo pueda dejar en una carpeta respectiva al proyecto, y por ultimo con la info que tengo me gustaria generar diagramas de secuencias, arquitectura o notas visuales para poder entenderlo de manera mas facil (si tienes ideas, eres libre de plantearla)."
- L2 (decisiones): multi-OS; local-first; PC RTX 4070 8 GB + MacBook M5 Air 16 GB; Analyzer como adaptador (Ollama o suscripción, a elección del usuario); stack Python.
- L3 (entorno 2026-10-18): sin Python ni `uv` en el PC; `python3` es solo el shim del Store; winget v1.29 disponible. Repo git con root en `C:/Users/ncanc` (home), sin commits — pendiente decisión de dónde vive el repo.
- L4 (decisiones usuario 2026-10-18): instalo Python + uv yo vía winget; repo git se decide después (sin commits por ahora).
- L11 (T8 done 2026-10-18): loop analyze→notes.md→SVG verificado — sequenceDiagram válido renderiza a SVG 191 KB. Fixes: render tolerante a fallos por bloque; prompt con ejemplo + temperature 0.2 (qwen metía prosa). Arquitectura vino vacía (criterio del modelo, v1 aceptable). mmdc necesita shell en Windows (.cmd shim) y Chromium de puppeteer.
- L10 (T7 done 2026-10-18): Analyzer Ollama verificado en vivo — `botmeet analyze` sobre transcript de ejemplo genera notes.md (summary/decisiones/actions/diagramas), 8 passed. Observaciones de calidad: qwen respondió en inglés aunque el transcript es español (el prompt pide mismo idioma, a mejorar); sequenceDiagram válido pero en una línea; architecture flojo. Adaptador Gemini pendiente (falta key de empresa).
- L9 (T5 done 2026-10-18): transcriptor verificado end-to-end en CUDA — `botmeet transcribe` genera `transcript.txt` (0 segmentos en demo silencioso, esperado). Batalla CUDA documentada: (1) av19 vs faster-whisper → decode manual a 16 kHz mono; (2) lock clavado en av14 sin wheel → pin av>=19; (3) loader nativo de ctranslate2 solo honra PATH → el adaptador antepone los bin/ NVIDIA. Test nuevo: test_transcriber.py. Falta prueba de calidad con voz real.
- L8 (T4 widget done 2026-10-18): widget flotante verificado offscreen — toggle start/stop graba WAV estéreo real (2.5 s), hotkey Ctrl+Shift+R registrado sin errores, pytest 3 passed. PySide6 6.12.0 + pynput 1.8.2 en extra `ui`. Import de UI lazy para no pesar en el CLI base.
- L7 (T4 engine done 2026-10-18): `capture.py` (sistema=L, mic=R) + CLI `botmeet record` verificados — smoke 5 s → WAV estéreo 48 kHz. Bug encontrado y fixeado: grabar ambos dispositivos secuencialmente partía el audio a la mitad y los desincronizaba; ahora un thread por dispositivo. Queda ~0.5 s de latencia de arranque (tolerable). Detalle: warnings "data discontinuity" de soundcard, inofensivos.
- L6 (T3 done 2026-10-18): scaffolding verificado — `uv sync` OK, pytest 1 passed. Estructura hexagonal-lite (ports como Protocol, adapters por tecnología). Decisión: sin DI framework.
- L5 (T1 PASS 2026-10-18): loopback WASAPI verificado — tono 880 Hz por default speaker capturado con pico exacto en 880.0 Hz, spectral_snr=1040.6. Lección: hay que grabar del loopback del MISMO dispositivo de salida (mics[0] era el monitor NVIDIA y daba silencio). Warnings de `soundcard`: "data discontinuity" (tolerables) y nombre con encoding roto ("Micrófono"). T2 macOS pendiente en la MacBook.
