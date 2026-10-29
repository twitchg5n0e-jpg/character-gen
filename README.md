# character-gen

Generiert symmetrische Game-Characters auf einer gemieteten GPU (z. B. RunPod).

- Die Scripts erzeugen pro Character 3 Ansichten: `front.png`, `links.png`, `hinten.png`
- GitHub Actions erzeugt danach automatisch `rechts.png` (gespiegelte linke Ansicht)

## Ordnerstruktur

```
scripts/        deine Generierungs-Scripts
output/<name>/  front.png, links.png, hinten.png, rechts.png (+ Modelle)
run_pod.sh      alles auf der GPU in einem Befehl
```

## Auf RunPod starten

```bash
git clone https://github.com/twitchg5n0e-jpg/character-gen.git
cd character-gen
bash run_pod.sh
```

`GITHUB_TOKEN` muss als Umgebungsvariable gesetzt sein (in RunPod als Secret).
Der Token braucht nur Zugriff auf **dieses** Repo ("Contents: Read and write").
