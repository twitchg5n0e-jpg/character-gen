# character-gen

Erzeugt die Vorlagebilder der Elyndra-Charaktere auf einer gemieteten GPU (z. B. RunPod). Prompts, Erzeugung und
Regeln liegen nur hier; das Elyndra-Repository bekommt die fertigen Bilder mit `scripts/copy_to_elyndra.py`.

- `scripts/generate.py` erzeugt mit ComfyUI + Qwen-Image pro Set 3 Ansichten: `front.png`, `links.png`, `hinten.png`
  (1056 × 1584, native Auflösung von Qwen-Image)
- GitHub Actions erzeugt danach automatisch `rechts.png` (gespiegelte linke Ansicht)
- Erzeugt werden die 88 Basismodelle (Body1) aus `scripts/sets.txt`: 20 Völker × 2 Geschlechter, die 8
  Wachstums-Völker in 4 Stufen. Alle 352 Sets (Body1 bis Body4) stehen in `scripts/sets_alle.txt`.
- Die Prompts stehen in `scripts/prompts/<Volk>/<Geschlecht>_<Body>_<Stufe>.md` und werden direkt dort geändert.
  Hintergrund zu Völkern und Regeln: [docs/Voelker_und_Regeln.md](docs/Voelker_und_Regeln.md).
- Hintergrund der Bilder: einfarbig hellgrau, ohne Boden, Horizont und Schatten, damit die Figur sauber freigestellt
  werden kann.

## Ordnerstruktur

```
scripts/generate.py         Bilder erzeugen (braucht laufendes ComfyUI)
scripts/setup_comfyui.sh    ComfyUI + Modelle installieren (~50 GB) und starten
scripts/comfyui/*.json      ComfyUI-Workflows (Text→Bild, Bild-Edit, Seiten- und Rückansicht)
scripts/prompts/            Prompts pro Set (die einzige Quelle)
scripts/sets.txt            Reihenfolge der Sets, die erzeugt werden (Body1)
scripts/sets_alle.txt       alle 352 Sets
scripts/copy_to_elyndra.py  fertige Sets als JPEG ins Elyndra-Repository kopieren
scripts/make_models.py      3D-Modelle aus den Ansichten (Hunyuan3D-2mv), make_models.sh auf der GPU
scripts/check_images.py     fertige Sets prüfen (Format, Hintergrund, abgeschnitten, Fey-/Merfolk-Farben)
docs/Voelker_und_Regeln.md  Völker, Stufen, Aufbau der Prompts
output/<Volk>_<Geschlecht>_<BodyX>_<StageX>/  front.png, links.png, hinten.png, rechts.png
run_pod.sh                  alles auf der GPU in einem Befehl
```

## Auf RunPod starten

```bash
git clone https://github.com/twitchg5n0e-jpg/character-gen.git
cd character-gen
bash run_pod.sh                                  # alle offenen Sets
LIMIT=1 bash run_pod.sh                          # nur das nächste Set (Test)
SET=Human/Female/Body1/Stage1 bash run_pod.sh    # genau dieses Set
BRANCH=claude/gifted-pasteur-7ee42l bash run_pod.sh   # auf diesem Branch arbeiten statt auf main
```

- Preis-Leistung: fp8-Modelle (kaum sichtbarer Unterschied zu bf16, halber Speicher), dafür 50 Schritte und
  native Auflösung, verlustfreies PNG.
- Günstigste passende GPU: RTX 4090 (24 GB) in der Community Cloud, am besten als Spot/Interruptible –
  ein Abbruch kostet höchstens das aktuelle Bild, neu starten macht weiter. Volume unter `/workspace` mit ~60 GB,
  damit die Modelle beim nächsten Pod nicht neu geladen werden müssen.
- Nach jedem fertigen Set wird gepusht; ein Abbruch verliert höchstens das aktuelle Bild. Erneut starten macht
  beim ersten fehlenden Bild weiter.
- Am Ende (auch bei einem Fehler) stoppt die GPU automatisch.
- Ein Bild neu machen: Datei in `output/` löschen, committen, pushen und `run_pod.sh` wieder starten.

`GITHUB_TOKEN` muss als Umgebungsvariable gesetzt sein (in RunPod als Secret).
Der Token braucht nur Zugriff auf **dieses** Repo ("Contents: Read and write").

## Lokal oder auf einem eigenen Rechner

Mit einer GPU ab 24 GB: `bash scripts/setup_comfyui.sh` (installiert und startet ComfyUI, Ordner über `COMFY_DIR`),
dann `pip install -r requirements.txt` und `python scripts/generate.py` (Optionen wie oben: `--limit`, `--set`).

## Bilder prüfen

```bash
python scripts/check_images.py                  # alle fertigen Sets
python scripts/check_images.py --sheets /tmp/s  # dazu ein Übersichtsbild pro Set
```

Meldet pro Set OK, WARNUNG (Hintergrund oben und unten verschieden, also Boden oder Verlauf) oder FEHLER
(fehlende oder falsche Datei, rechts kein Spiegelbild, Figur abgeschnitten oder zu klein, Fey einfarbig pink/lila,
Merfolk-Gesicht in Hautfarbe). Ein Set ohne Meldung sollte trotzdem jemand ansehen.

## 3D-Modelle

```bash
BRANCH=claude/gifted-pasteur-7ee42l bash scripts/make_models.sh   # auf der GPU, alle fertigen Sets ohne Modell
```

`scripts/make_models.py` macht aus den vier Ansichten jedes fertigen Sets mit Hunyuan3D-2mv eine Form, entfernt
Schwebeteile, reduziert auf 150 000 Dreiecke und bemalt sie mit den Farben der Vorlagebilder (Vertexfarben, ohne
KI-Textur). Ergebnis: `models/<Set>/model.glb` und `models/<Set>/vorschau.png` (vorn, links, hinten, rechts).
Etwa 3–4 Minuten pro Modell auf einer RTX 4090. Die Modelle sind roh: für das Spiel brauchen sie noch Retopologie
und ein Skelett.

## In Elyndra übernehmen

```bash
python scripts/copy_to_elyndra.py /pfad/zu/Elyndra
```

Kopiert jedes vollständige Set als JPEG 1024 × 1536 nach
`Assets/Characters/Races/<Volk>/<Geschlecht>/<Body>/<Stufe>/References/`; Elyndras Workflow hakt sie dann in
`REFERENCE_PROGRESS.md` ab.
