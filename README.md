# character-gen

Generiert symmetrische Game-Characters auf einer gemieteten GPU (z. B. RunPod).

- `scripts/generate.py` erzeugt mit ComfyUI + Qwen-Image pro Character 3 Ansichten: `front.png`, `links.png`, `hinten.png` (1056 × 1584, native Auflösung von Qwen-Image)
- GitHub Actions erzeugt danach automatisch `rechts.png` (gespiegelte linke Ansicht)
- Es sind die 352 Elyndra-Sets (20 Völker × 2 Geschlechter × 4 Erscheinungen, Wachstums-Völker in 4 Stufen),
  Reihenfolge in `scripts/sets.txt`, Prompts in `scripts/prompts/`

## Ordnerstruktur

```
scripts/generate.py         Bilder erzeugen (braucht laufendes ComfyUI)
scripts/setup_comfyui.sh    ComfyUI + Modelle installieren (~50 GB) und starten
scripts/comfyui/*.json      ComfyUI-Workflows (Text→Bild, Bild-Edit)
scripts/prompts/            Prompts pro Set
scripts/sets.txt            Reihenfolge der Sets
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
