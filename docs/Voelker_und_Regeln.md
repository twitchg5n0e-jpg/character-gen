# Völker und Prompt-Regeln

Hintergrund zu den Vorlagebildern: Völker, Stufen, Aufbau der Prompts und die Regeln dahinter. Die Datei kommt aus
Elyndra (`Assets/Characters/References/REFERENCE_PROMPTS.md`) und ist dort entfernt.

**Die gültigen Prompts stehen in [`scripts/prompts/`](../scripts/prompts/)** und werden direkt dort geändert;
`scripts/generate.py` liest nur diese Dateien. Die Prompt-Texte weiter unten sind der ursprüngliche Entwurf und weichen
inzwischen ab (z. B. keine Kleidung bei Völkern mit Fell, Federn, Schuppen, Stein oder Rinde, freistellbarer
Hintergrund, Merfolk mit Fischgesicht, Fey als edle Waldfee mit Blätter-und-Blüten-Mieder ohne Maske und Fell). Pfade wie `Assets/...` und `Tools/...` beziehen
sich auf das Elyndra-Repository.

## Überblick

| | Anzahl | Werte |
| --- | --- | --- |
| Völker | 20 | Human, HighElf, DarkElf, Dwarf, Halfling, Beastfolk, Dragonborn, WoodElf, Gnome, Orc, Goblin, Troll, Ogre, Lizardfolk, Birdfolk, Merfolk, Demonborn, Fey, Stoneborn, Plantfolk |
| Geschlechter | 2 | Female, Male |
| Erscheinungen | 4 | Body1 Athletisch, Body2 Schlank, Body3 Kräftig, Body4 Stämmig |
| Stufen | 4 | Stage1 bis Stage4 (Level 1, 10, 25, 50) |
| **Sets** | **352** | je Set drei Bilder: 12 Runen-Völker nur Stage1 (96), 8 Wachstums-Völker alle vier Stufen (256) |

Die Runen-Völker brauchen nur Bilder der Stufe 1: Ihre Runen malt keine Bild-KI, sie kommen in Unreal als
Textur-Ebene mit regelbarem Leuchten auf das Stage1-Modell (siehe „Runen und Wachstum“).

Ein Set liegt in `Assets/Characters/Races/<Race>/<Gender>/<Body>/<Stage>/References/` als `01_Front.jpg`,
`02_Ruecken.jpg` und `03_Links.jpg` (JPEG, 1024 × 1536). Die rechte Ansicht `04_Rechts` ist das Spiegelbild von
`03_Links` und wird nicht gespeichert (`python Tools/Characters/make_right_views.py` erzeugt sie bei Bedarf).

## Aufbau eines Prompts

```
Geschlecht + Volk + Female- oder Male-Zeile + Erscheinung + Stufe + Runen oder Wachstum des Volkes + Grundprompt + Ansicht
```

Geschlecht und Volk stehen vorne, weil Bildmodelle den Anfang des Prompts am stärksten gewichten; stand der lange
Grundprompt vorne, wurden Frauen im Test oft zu männlichen Körpern. Dazu der Negativ-Prompt mit den Zusätzen des
Geschlechts und des Volkes. Vorlagen beim Erzeugen:

- `Stage1/01_Front` jeder Erscheinung entsteht nur aus dem Prompt (Qwen-Image).
- `02_Ruecken` und `03_Links` entstehen mit Qwen-Image-Edit aus dem `01_Front` desselben Sets.
- `01_Front` der Stufen 2 bis 4 (nur Wachstums-Völker) entsteht mit Qwen-Image-Edit aus dem `Stage1/01_Front`
  derselben Erscheinung, damit Gesicht und Körper gleich bleiben.

Ein vollständiges Beispiel steht am Ende.

## Grundprompt

```text
High-quality realistic character render of a fantasy RPG character, in the style of a modern AAA game made in
Unreal Engine 5 with scanned, lifelike humans: realistic skin with visible pores, fine surface detail and subtle
natural color variation, natural subsurface scattering, sharp focus, high detail; not plastic, not clay, not a doll.
Full body, standing straight in a relaxed A-pose, arms slightly away from the body, feet shoulder-width apart,
barefoot. Bald head with no hair, no beard; the ears exactly as described for the race above, and species
features such as fur, feathers, scales or horns stay. The default base body of a game character creator, with
the female or male body shape and muscles described above, wearing only the simple underwear described above:
plain, seamless, matte dark gray fabric that fits tightly like a second skin, with no logos, no patterns and no
lace; arms, legs, belly, back, shoulders and face are bare skin; fur, scales, feathers, stone or bark cover the
body where the race has them. No jewelry, no weapons.
Neutral calm expression, mouth closed. Plain neutral light gray studio background, soft even diffuse studio
lighting, no rim light, no shadows on the background. Camera at chest height with a long lens, almost no
perspective distortion. The whole figure is centered and fully in frame from the top of the head to the toes,
including any tail, wings or horns, with a little space above and below. Portrait format 2:3.
One single image showing one single character from one single camera angle; not a character sheet, not a
turnaround, not a collage.
```

Alle Völker tragen nur **schlichte, enge Unterwäsche** in mattem Dunkelgrau, die wie eine zweite Haut anliegt: ein
Grundkörper wie im Charakter-Editor eines Spiels, mit realistischer Haut statt Plastik-Look. Ganz ohne Kleidung
lehnt Tripo die Bilder ab (Inhaltsrichtlinie), und enge Wäsche ohne Falten stört das 3D-Modell kaum. Kleidung und Rüstung kommen im Spiel als eigene, abnehmbare Teile dazu
(`Assets/Characters/Clothing/`).

## Negativ-Prompt

```text
hair on the head, beard, old, elderly, aged, older face, mature face, aged face, crow's feet, hard weathered face,
wrinkles, gray hair, gray fur, sagging skin, nude, naked, topless, bare breasts, nipples, genitals, pubic hair,
lingerie, lace, bikini, swimsuit, loose clothing, shirt, pants, skirt, folds in the fabric, colorful underwear,
erotic, sexual, suggestive pose, belts, straps, pouches, shoes, jewelry, weapons, armor, cropped feet, cropped head, cropped tail,
dramatic shadows, rim light, fisheye, perspective distortion, open mouth, colored background, blue background,
stock photo, fashion photo, glamour, body paint, war paint, face paint, runes on the face, runes on the chest,
ornaments on the chest, ornaments on the belly, neck tattoo, collar, necklace, lace pattern, henna, mehndi,
white tattoo, three-quarter view, white background, plastic skin, waxy skin, clay, doll, toy, mannequin,
cartoon, stylized, airbrushed, stickers, decals, text, watermark, multiple characters, collage, character sheet, turnaround sheet, multiple
views, several poses, split image, side by side, grid, panels, border, frame
```

Zusätze pro Volk stehen beim Volk unter „Negativ zusätzlich“, Zusätze pro Geschlecht unter „Geschlecht“.

## Geschlecht

Steht am Anfang jedes Prompts, damit das Modell zuerst erfährt, wen es zeichnet. `{race}` ersetzt der Generator
durch den Namen des Volkes (`HighElf` wird `High Elf`).

**Female**
```text
One young adult woman: a female {race} character with a clearly feminine face and figure: a modest bust, a
slightly narrower waist and slightly wider hips than a man of her race. She wears a simple fitted sports-bra top
and fitted briefs.
```

**Negativ Female:** `man, male, masculine body, male torso, flat male chest, areolas, large breasts, voluptuous, curvy, exaggerated hips`

**Male**
```text
One young adult man: a male {race} character with a clearly masculine face and figure: a flat chest, a
straight waist and narrower hips than a woman of his race. He wears simple fitted boxer briefs and nothing on
his upper body.
```

**Negativ Male:** `woman, female, feminine body, breasts`

## Erscheinungen

Jedes Volk und Geschlecht gibt es in vier Erscheinungen, damit man im Charakter-Editor Gesicht und Körperbau
wählen kann. Grösse und Merkmale des Volkes bleiben; Körperbau, Gesicht und ein leicht anderer Haut-, Fell- oder
Schuppenton ändern sich. Die Runenzeichen sind bei allen vier Erscheinungen eines Volkes gleich.

**Body1 (Athletisch)**
```text
Appearance variant: balanced. Athletic, well-proportioned build typical of the race; oval face with balanced
features, medium straight nose, almond-shaped eyes. These differences override the build described above; the
height and features of the race stay.
```

**Body2 (Schlank)**
```text
Appearance variant: slender. Noticeably slimmer and leaner than average for the race, long limbs, little muscle
bulk; narrow angular face with high cheekbones, fine straight nose and narrow chin; skin, fur or scales a shade
lighter. These differences override the build described above; the height and features of the race stay.
```

**Body3 (Kräftig)**
```text
Appearance variant: powerful. Noticeably broader and more muscular than average for the race, thick neck,
shoulders and arms; square face with a strong wide jaw, broad nose and heavy brows; skin, fur or scales a shade
darker. These differences override the build described above; the height and features of the race stay.
```

**Body4 (Stämmig)**
```text
Appearance variant: sturdy. Compact, solid and slightly heavier build with a soft layer over the muscles, wide
hips and waist; round face with full cheeks, short wide nose and large round eyes; skin, fur or scales a warmer
shade. These differences override the build described above; the height and features of the race stay.
```

## Stufen

Die Stufen sind **Level-Stufen, keine Altersstufen**: Gesicht, Alter und Grundkörper bleiben gleich. Alle vier
Stufen nennen dasselbe Alter (etwa 22) und keine Wörter wie „veteran“, „legendary“ oder „seasoned“, weil
Bildgeneratoren die Figur sonst älter machen. Die Stufe zeigt sich an den Runen oder am Wachstum des Volkes und an
einem etwas trainierteren Körper.

| Stufe | Ordner | ab Level | Runen | Wachstum |
| --- | --- | --- | --- | --- |
| 1 | `Stage1` | 1 | keine | schlicht |
| 2 | `Stage2` | 10 | Schutz-Band um jeden Unterarm, dunkel | erste Veränderung, Farbe beginnt sich zu ändern |
| 3 | `Stage3` | 25 | dazu Weg-Ornament an jedem Unterschenkel, leicht leuchtend | deutlich prächtiger, Farbe deutlich verändert |
| 4 | `Stage4` | 50 | dazu Kraft-Armreife an den Oberarmen und Emblem-Medaillon zwischen den Schulterblättern, hell leuchtend | am prächtigsten, Farbe am stärksten verändert |

**Stufe 1 (`Stage1`)**
```text
About 22 years old for their kind, youthful face with smooth skin, a fresh adventurer, natural relaxed upright
posture.
```

**Stufe 2 (`Stage2`)**
```text
About 22 years old for their kind, exactly the same youthful face and age as at stage 1, smooth skin. The only
changes are the ones described below and a slightly more toned body.
```

**Stufe 3 (`Stage3`)**
```text
About 22 years old for their kind, exactly the same youthful face and age as at stage 1, smooth skin, no
wrinkles. The only changes are the ones described below and a slightly more toned body.
```

**Stufe 4 (`Stage4`)**
```text
About 22 years old for their kind, exactly the same youthful face and age as at stage 1, smooth skin, no
wrinkles. The only changes are the ones described below and a slightly more toned body.
```

## Runen und Wachstum

**Zwölf Völker tragen Runen:** Human, HighElf, DarkElf, Dwarf, Halfling, WoodElf, Gnome, Orc, Goblin, Troll, Ogre,
Demonborn.

- **Stil und Farbe pro Volk:** Jedes Volk hat einen eigenen Ornament-Stil und eine eigene Leuchtfarbe; keine zwei
  Völker teilen eine Farbe.
- **Zeichen pro Volk:** Body1 bis Body4 tragen dieselben Zeichen (Zeile `Zeichen` beim Volk), damit die Runen
  ein Erkennungsmerkmal des Volkes sind.
- **Jedes Zeichen bedeutet etwas:**

  | Zeichen | Bedeutung | Ort | ab Stufe |
  | --- | --- | --- | --- |
  | Schutz | hat die ersten Kämpfe überstanden | Ornamentband um jeden Unterarm | 2 |
  | Mut | stellt sich jeder Gefahr | kleines Zeichen auf jedem Handrücken | 2 |
  | Weg | ist weit gereist | schmales Ornament aussen am Unterschenkel | 3 |
  | Ausdauer | hält jede Mühe durch | schmales Ornament aussen an jedem Oberschenkel | 3 |
  | Kraft | ist stark geworden | Armreif-Ornament um jeden Oberarm | 4 |
  | Emblem | ist eine Legende des Volkes | handgrosses Medaillon zwischen den Schulterblättern | 4 |
  | Ruhm | wird überall besungen | kleines Zeichen auf jedem Schulterblatt, neben dem Medaillon | 4 |

- **Aussehen:** kräftiges Tattoo mit dicken, dunklen Linien (bei Stein und Rinde eingeritzt); die Rune gross und
  gut lesbar als Mittelstück, nur wenig Verzierung drumherum, keine feine Spitze und kein Henna. Nur Akzente, der
  grösste Teil der Haut bleibt frei; nie im Gesicht oder auf der Brust. Stufe 2 dunkel, Stufe 3 leicht und
  Stufe 4 hell leuchtend; das Leuchten kommt aus den dunklen Linien, die Linien werden nicht weiss.
- **Menschen** tragen echte Runen des älteren Futhark (Schutz: Algiz; Kraft: Uruz; Weg: Ehwaz; Emblem: Othala),
  die anderen Völker eigene Bildzeichen.
- **Technik:** Die Stufen-Zeilen enthalten `{protection}`, `{courage}`, `{journey}`, `{endurance}`,
  `{strength}`, `{emblem}`, `{glory}` und `{color}`.
  Der Generator setzt die Zeichen des Volkes (Zeile `Zeichen`) und seine Farbe ein.
- **Nicht im Bild, sondern in Unreal:** Die Bild-KI zeichnete die Runen im Test unbrauchbar (ganze Ärmel, Runen
  auf der Brust, nur an einem Bein, feine weisse Spitze). Deshalb entstehen für die Runen-Völker nur Bilder und
  Modelle der Stufe 1; die Runen kommen in Unreal als Textur-Ebene mit Leuchten auf dieses Modell. Die Stufen-Zeilen
  beim Volk und die folgenden Regeln sind die Vorlage für diese Texturen, der Prompt-Generator nutzt sie nicht.

  **Runen-Regeln**
  ```text
  Bold tattoo style: thick, clean, solid dark ink lines; the rune itself is large, bold and clearly readable at
  the center of each ornament, with only a little decoration around it. Not fine lace, not henna, not thin
  filigree. Where the lines glow, the glow shines from inside the dark lines; the lines do not turn white.
  The ornaments appear only in the places named above. The chest, breasts, belly, collarbones, neck, shoulders
  and face stay completely bare skin with no lines, patterns or markings at all. The ornaments use only the
  dark ink or the glow color described, no other colors.
  ```

**Acht Völker wachsen statt Runen:** Beastfolk, Dragonborn, Lizardfolk, Birdfolk, Merfolk, Fey, Stoneborn,
Plantfolk. Bei ihnen werden Fell und Krallen, Hörner und Stacheln, Kragen und Kamm, Federn, Flossen und
Leuchtpunkte, Flügelmuster, Kristalle oder Blätter und Blüten von Stufe zu Stufe prächtiger, und die Farbe von Fell,
Schuppen, Federn, Haut, Stein oder Rinde ändert sich, aber nicht bei allen gleich: **intensiver** bei Beastfolk und
Plantfolk, **dunkler** bei Dragonborn und Stoneborn, **heller** bei Lizardfolk und Birdfolk, **zarter und blasser**
bei Merfolk und Fey. Was genau, steht beim Volk unter „Wachstum statt Runen“.

## Design-Regeln

- **Silhouette zuerst:** Jedes Volk hat ein Merkmal, das man schon als Umriss erkennt (Ohren, Hörner, Hauer,
  Flügel, Schwanz, Körpergrösse). Es steht im Prompt als `Signature:`.
- **Formsprache:** rund und weich wirkt freundlich (Halfling, Gnome), schmal und gestreckt elegant (HighElf, Fey),
  kantig und spitz gefährlich (DarkElf, Demonborn, Dragonborn), breit und schwer stark (Dwarf, Orc, Ogre, Stoneborn).
- **3D-tauglich:** Schwänze und Ohren stehen ein Stück vom Körper ab, Flügel bleiben klein und angelegt und sind
  nicht durchsichtig, Hände bleiben frei. Nichts, was ein 3D-Modell schlecht abbilden kann (Rauch, Feuer, Glas, durchsichtige Haut).
- **Aufbau pro Volk:** Beschreibung für beide Geschlechter, je eine Zeile Female und Male, dann Runen oder
  Wachstum mit den vier Stufen und die Negativ-Zusätze.

## Völker

### Human

```text
Human, natural realistic proportions, athletic toned build, warm light skin, natural eye color, normal rounded
ears. Signature: grounded heroic look, the baseline all other races are compared to.
```

**Female:** `Female, about 170 cm tall, athletic and toned, defined but not bulky muscles.` ·
**Male:** `Male, about 182 cm tall, strong muscular athletic build, broad shoulders, defined chest and arms.`

**Runen (nordische Runen, Farbe Silberweiß `silver-white`):**

- Zeichen: Schutz `the rune Algiz (a vertical stroke with two arms pointing up)` · Kraft `the rune Uruz (an upside-down U with a slanted top)` · Weg `the rune Ehwaz (an angular M)` · Emblem `the heritage rune Othala (a diamond standing on two legs) in a ring of runes` · Mut `the rune Tiwaz (an arrow pointing up)` · Ausdauer `the rune Eihwaz (a vertical stroke with opposite hooks)` · Ruhm `the rune Sowilo (an angular S, the sun of victory)`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: Norse knotwork with interlaced bands with the protection rune, {protection}, woven in as its centerpiece, angular Norse runes of the Elder Futhark, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, Norse knotwork with interlaced bands: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, Norse knotwork with interlaced bands: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `pointed ears, elf ears`

### HighElf

```text
High Elf, tall, slender and elongated proportions: long neck, long arms and legs, very little muscle mass,
elegant and ethereal, clearly not human. Flawless pale porcelain skin with a faint pearlescent golden sheen,
luminous golden eyes, thin fine pale eyebrows, refined angular face with high sharp cheekbones and a narrow
chin, large almond-shaped eyes. Signature: long slender swept-back pointed ears that rise above the top of the
head.
```

**Female:** `Female, about 185 cm tall, narrow shoulders, narrow waist, slim willowy figure, small bust.` ·
**Male:** `Male, about 195 cm tall, slim shoulders, lean swimmer-like build with only light muscle definition.`

**Runen (Ranken-Filigran, Farbe Gold `gold`):**

- Zeichen: Schutz `a leaf-shaped eye` · Kraft `a rising sun with fine rays` · Weg `a path of falling leaves` · Emblem `a great tree of light with roots and branches` · Mut `an eight-pointed star` · Ausdauer `an evergreen laurel stem` · Ruhm `a laurel wreath around a star`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: flowing elven filigree with curling vines and leaves with the protection rune, {protection}, woven in as its centerpiece, fine flowing elven filigree script, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, flowing elven filigree with curling vines and leaves: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, flowing elven filigree with curling vines and leaves: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `bulky muscles, broad shoulders, tan skin, blue eyes, brown eyes, short ears`

### DarkElf

```text
Dark Elf, dark ash-gray skin with a cool violet undertone, deep gray-violet, not pink, not light purple.
Glowing pale violet eyes, sharp angular elegant features, high cheekbones, narrow nose. Signature: long sharp
pointed ears angled up and back, and the dark gray-violet skin.
```

**Female:** `Female, about 172 cm tall, slender athletic figure, toned defined muscles.` ·
**Male:** `Male, about 185 cm tall, strong athletic build with defined muscles, broad shoulders.`

**Runen (dornige Glyphen, Farbe Violett `violet`):**

- Zeichen: Schutz `a small spider-web shield` · Kraft `a crescent moon with thorns` · Weg `a line of small stars` · Emblem `a spider crowned by a crescent moon` · Mut `a curved blade` · Ausdauer `a spider web` · Ruhm `a spiked crown below a crescent`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: thorny lace and spider-web tracery with the protection rune, {protection}, woven in as its centerpiece, sharp thorny glyphs, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, thorny lace and spider-web tracery: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, thorny lace and spider-web tracery: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `pink skin, light skin, pale skin, lavender skin, human skin tone`

### Dwarf

```text
Dwarf, short, stocky and very broad, heavy bones, thick strong arms and legs, large hands and feet, warm ruddy
skin, round strong face with a broad nose and heavy brow, small deep-set eyes, normal rounded ears.
Signature: almost as wide as tall, a compact powerful block of muscle.
```

**Female:** `Female, about 130 cm tall, wide hips and shoulders, strong and muscular.` ·
**Male:** `Male, about 135 cm tall, barrel chest, very broad shoulders, massive arms.`

**Runen (Schmiederunen, Farbe Kupfer `copper`):**

- Zeichen: Schutz `a square shield rune with a cross` · Kraft `a hammer rune` · Weg `a stair-step line` · Emblem `an anvil with two crossed hammers` · Mut `a double-bitted battle axe` · Ausdauer `a mountain` · Ruhm `a crown with square gems`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: geometric Dwarven knot bands with straight interlocking lines with the protection rune, {protection}, woven in as its centerpiece, angular geometric forge runes in straight bands, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, geometric Dwarven knot bands with straight interlocking lines: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, geometric Dwarven knot bands with straight interlocking lines: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `tall, slim, long legs, pointed ears, elf ears`

### Halfling

```text
Halfling, small, human-like adult proportions at a small scale, clearly adult, rosy warm skin with freckles,
round friendly face, bright hazel eyes, slightly pointed small ears. Signature: large bare feet with hairy tops
and a cheerful round face.
```

**Female:** `Female, about 110 cm tall, soft rounded figure.` ·
**Male:** `Male, about 115 cm tall, sturdy compact build.`

**Runen (Blatt- und Rankenlinien, Farbe Rosa `rose-pink`):**

- Zeichen: Schutz `a round hearth circle` · Kraft `an acorn` · Weg `a small bird in flight` · Emblem `a large home tree with a round door` · Mut `a small sword` · Ausdauer `a walking staff with a bundle` · Ruhm `a wreath of flowers`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: soft leafy vine scrolls with the protection rune, {protection}, woven in as its centerpiece, soft rounded leaf-and-vine lines, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, soft leafy vine scrolls: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, soft leafy vine scrolls: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `child, childlike face, baby proportions`

### Beastfolk

```text
Beastfolk tiger humanoid, tiger head with a feline muzzle, whiskers and round tiger ears, amber eyes, orange fur
with bold black stripes and cream-white fur on the belly, chest and inner arms, clawed hands with five fingers,
digitigrade legs with large paw feet. Fur covers the whole body, with short fur on the head.
Signature: tiger head and a long striped tail held away from the legs.
```

**Female:** `Female, about 180 cm tall, athletic slender predator build.` ·
**Male:** `Male, about 195 cm tall, broad powerful build, thick neck and shoulders.`

**Wachstum statt Runen (Fell und Krallen, Farbe):**

- Stufe 1: `Short sleek fur, normal claws.`
- Stufe 2: `The fur is a little thicker and the black stripes are bolder and sharper; the claws are slightly longer. The orange fur turns a deeper, warmer orange.`
- Stufe 3: `Thick glossy fur with bold, almost black stripes, a short ruff of longer fur around the neck and shoulders, longer curved claws, the amber eyes shine brighter. The fur is a rich red-orange with a faint golden sheen.`
- Stufe 4: `A proud thick ruff of longer fur around the neck, shoulders and upper back like a short mane, deep bold stripes, long strong claws, the amber eyes glow softly. The fur is a deep red-gold with shining golden tips, the cream fur bright and clean.`

**Negativ zusätzlich:** `human face, human skin showing, long hair on the head, fur missing on the body, runes, tattoos`

### Dragonborn

```text
Dragonborn, dragon head with a short strong snout, golden reptile eyes with slit pupils, a small crest of spikes
on the head, deep blue scales with pale silver-white belly scales, clawed hands, clawed
digitigrade feet. Scales cover the whole body. Signature: two curved dark horns sweeping back and a long thick
scaled tail held away from the legs.
```

**Female:** `Female, about 185 cm tall, athletic slender build.` ·
**Male:** `Male, about 200 cm tall, broad powerful build, thick neck, heavy chest.`

**Wachstum statt Runen (Hörner, Stacheln und Schuppen, Farbe):**

- Stufe 1: `Short horns and a small crest of spikes on the head.`
- Stufe 2: `The horns are a little longer and the crest of spikes reaches down the neck. The blue scales turn a deeper, richer blue.`
- Stufe 3: `Long swept-back horns, a ridge of spikes running from the head down the spine to the tail, the scales have a slight metallic sheen. The scales are deep sapphire blue with silver edges.`
- Stufe 4: `Grand long curved horns, a row of large spikes along the spine and tail, gleaming metallic scales, and the pale belly and throat scales glow faintly cyan. The scales are a dark midnight blue with gleaming silver-cyan edges.`

**Negativ zusätzlich:** `human face, human skin showing, wings, runes, tattoos`

### WoodElf

```text
Wood Elf, medium height, lithe agile build, sun-kissed copper-tan skin with light freckles, bright leaf-green
eyes, natural wild sharp features. Signature: medium-long pointed ears angled back.
```

**Female:** `Female, about 168 cm tall, lithe and athletic.` ·
**Male:** `Male, about 178 cm tall, lithe athletic build with defined lean muscles.`

**Runen (Blatt- und Zweigmuster, Farbe Moosgrün `moss-green`):**

- Zeichen: Schutz `an oak leaf` · Kraft `an antler` · Weg `a line of fox tracks` · Emblem `a stag whose antlers grow into tree branches` · Mut `an arrow` · Ausdauer `a pine tree` · Ruhm `a hunting horn`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: intertwined branches and leaves with the protection rune, {protection}, woven in as its centerpiece, leaf-and-branch patterns, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, intertwined branches and leaves: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, intertwined branches and leaves: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `porcelain skin, golden eyes`

### Gnome

```text
Gnome, very small, large head in proportion, very large bright blue eyes, fair rosy skin, curious clever
expression. Signature: oversized eyes, a big round nose and medium pointed ears sticking out to the sides.
```

**Female:** `Female, about 95 cm tall, slight delicate build, button nose.` ·
**Male:** `Male, about 100 cm tall, slight wiry build, prominent round nose.`

**Runen (Zahnrad- und Schaltkreislinien, Farbe Elektrisches Cyanblau `electric cyan-blue`):**

- Zeichen: Schutz `a cog with a keyhole` · Kraft `a lightning bolt in a gear` · Weg `a chain of small gears` · Emblem `a great clockwork gear with a star at its center` · Mut `a wrench` · Ausdauer `a coiled spring` · Ruhm `a lantern`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: fine clockwork filigree with gears and circuit lines with the protection rune, {protection}, woven in as its centerpiece, clockwork circuit lines, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, fine clockwork filigree with gears and circuit lines: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, fine clockwork filigree with gears and circuit lines: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `child, baby, pointed hat, beard`

### Orc

```text
Orc, tall and powerful, deep olive-green skin, strong square jaw, heavy brow ridge, short pointed ears, amber
eyes, fierce proud expression. Signature: lower tusks jutting up from the jaw and a massive V-shaped upper body.
```

**Female:** `Female, about 185 cm tall, muscular athletic build, two small lower tusks.` ·
**Male:** `Male, about 200 cm tall, very muscular heavy build, broad shoulders, two large lower tusks.`

**Runen (Kriegsglyphen, Farbe Blutrot `blood-red`):**

- Zeichen: Schutz `a pair of tusks` · Kraft `a clenched fist` · Weg `a line of boar tracks` · Emblem `a tusked skull above two crossed axes` · Mut `a war axe` · Ausdauer `a war drum with two sticks` · Ruhm `a horned helmet`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: bold jagged tribal bands with the protection rune, {protection}, woven in as its centerpiece, bold jagged war glyphs, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, bold jagged tribal bands: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, bold jagged tribal bands: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

### Goblin

```text
Goblin, small, wiry skinny build, long thin arms with long fingers, slightly hunched, yellow-green skin, large
yellow eyes, sharp small teeth, pointed nose, sly mischievous grin. Signature: huge long pointed ears sticking
far out to the sides.
```

**Female:** `Female, about 105 cm tall.` · **Male:** `Male, about 110 cm tall, long pointed nose.`

**Runen (krakelige Zeichen, Farbe Giftiges Limettengrün `toxic lime-green`):**

- Zeichen: Schutz `an eye with a zigzag` · Kraft `a crooked dagger` · Weg `a line of rat tracks` · Emblem `a grinning moon face` · Mut `a crooked arrow` · Ausdauer `a sack of loot` · Ruhm `a crooked crown`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: crooked zigzag bands with the protection rune, {protection}, woven in as its centerpiece, crude scratchy symbols, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, crooked zigzag bands: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, crooked zigzag bands: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `child, baby, cute`

### Troll

```text
Troll, very tall and lanky, slightly hunched, very long arms reaching the knees, large hands and feet, gray-blue
skin with a rough leathery texture, long pointed nose, long drooping ears, small yellow eyes. Signature: the long
dangling arms and two tusks curving upward from the lower jaw.
```

**Female:** `Female, about 240 cm tall, two small tusks.` ·
**Male:** `Male, about 260 cm tall, lanky but powerful, two larger tusks.`

**Runen (Spiral- und Knochensymbole, Farbe Petrol `teal`):**

- Zeichen: Schutz `a spiral` · Kraft `a bone club` · Weg `a river spiral` · Emblem `a huge spiral with bones radiating from it` · Mut `three claw marks` · Ausdauer `a heart with a spiral` · Ruhm `a totem mask with tusks and feathers`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: large primitive spirals with the protection rune, {protection}, woven in as its centerpiece, large primitive symbols, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, large primitive spirals: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, large primitive spirals: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

### Ogre

```text
Ogre, huge and massive, heavy body with thick limbs, very broad shoulders, mottled grayish-tan skin, small eyes,
broad flat nose, heavy jaw. Signature: enormous bulk with a big belly and two lower tusks.
```

**Female:** `Female, about 270 cm tall, thick waist and belly, two small lower tusks.` ·
**Male:** `Male, about 300 cm tall, big round belly, enormous arms, heavy underbite with two lower tusks.`

**Runen (Clanzeichen, Farbe Tiefes Marineblau `deep navy-blue`):**

- Zeichen: Schutz `a boulder block` · Kraft `a fist on a block` · Weg `a large boot print` · Emblem `a fist crushing a mountain` · Mut `a club` · Ausdauer `a ham bone` · Ruhm `a crown of boulders`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: heavy blocky interlocking bands with the protection rune, {protection}, woven in as its centerpiece, heavy blocky clan symbols, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, heavy blocky interlocking bands: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, heavy blocky interlocking bands: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

### Lizardfolk

```text
Lizardfolk, reptile humanoid with a long crocodile-like snout, no ears, yellow eyes with slit pupils, green
scales with a lighter yellow-green belly, clawed hands, clawed feet. Scales cover the whole body. Signature: long heavy tail held away from the legs and a frill of spines on
the back of the head.
```

**Female:** `Female, about 180 cm tall, lean athletic build, small head frill.` ·
**Male:** `Male, about 195 cm tall, broad muscular build, larger head frill.`

**Wachstum statt Runen (Kragen, Rückenkamm und Farben, Farbe):**

- Stufe 1: `A small frill of spines on the back of the head.`
- Stufe 2: `The head frill is a little larger. The green scales turn a lighter, brighter green.`
- Stufe 3: `A large head frill, a ridge of armored scales and small spikes down the back to the tail, pale yellow scale patterns. The scales are a bright light jade green with pale golden flecks.`
- Stufe 4: `A large fan-shaped head frill with bright yellow edges, a prominent spiked ridge down the back and tail, a faint golden sheen. The scales are a luminous pale jade and light gold, much lighter than at the start.`

**Negativ zusätzlich:** `human face, human skin showing, horns, blue scales`

### Birdfolk

```text
Birdfolk, bird humanoid with a hawk-like head and hooked beak, golden eyes, brown and cream feathers covering the
whole body, scaled bird legs with talons, short fanned tail feathers. Short compact feathers along the
back of each arm, lying flat against the arm, hands stay free with three clawed fingers; no large wings. Signature:
hawk head and the feathered arms.
```

**Female:** `Female, about 170 cm tall, light slender build, shorter beak.` ·
**Male:** `Male, about 180 cm tall, lean wiry build.`

**Wachstum statt Runen (Federn und Kamm, Farbe):**

- Stufe 1: `Short crest feathers on the head, plain brown and cream plumage.`
- Stufe 2: `Slightly longer crest feathers. The brown feathers turn a lighter tan.`
- Stufe 3: `A tall crest of feathers on the head, bold banded patterns on the arm feathers, sharper talons. The feathers are a light sandy gold, the cream feathers almost white.`
- Stufe 4: `A magnificent tall crest, arm and tail feathers with bright sky-blue tips, striking banded patterns, the golden eyes shine brightly. The feathers are a bright pale silver-gold with white chest feathers, much lighter than at the start.`

**Negativ zusätzlich:** `human face, large wings, spread wings, wings on the back, long flight feathers, flying`

### Merfolk

```text
Merfolk on legs, pale blue-green skin with a pearly shimmer, patches of small aqua scales on the shoulders, hips
and outer legs, gill slits on the sides of the neck, webbed fingers and toes, small fins on the forearms and
ankles, large dark aquamarine eyes. Signature: fan-shaped fin ears and the fins on forearms and ankles.
```

**Female:** `Female, about 172 cm tall, slender athletic swimmer build.` ·
**Male:** `Male, about 185 cm tall, lean muscular swimmer build with broad shoulders.`

**Wachstum statt Runen (Flossen und Leuchtpunkte, Farbe):**

- Stufe 1: `Small fins on the forearms and ankles, small fan-shaped fin ears.`
- Stufe 2: `Slightly larger fins and a few faint bioluminescent aqua dots along the collarbones. The blue-green skin turns a softer, paler blue-green.`
- Stufe 3: `Larger, more translucent-looking fins with colored edges, and rows of softly glowing bioluminescent aqua dots along the arms and legs. The skin is a pale, delicate sea-foam color with a soft pearly sheen, the scale patches light aqua.`
- Stufe 4: `Long flowing fins on the forearms, ankles and ears with bright aqua edges, and many bioluminescent aqua dots forming patterns along the arms, legs and back. The skin is an airy pale pearl with a faint sea-foam tint, almost translucent-looking, the scale patches soft silver-aqua.`

**Negativ zusätzlich:** `fish tail instead of legs, mermaid tail, water, wet`

### Demonborn

```text
Demonborn, human-like body, deep crimson-red skin, solid glowing golden eyes without pupils, slightly pointed
ears, sharp angular features, black fingernails. Signature: two curved black horns rising from the forehead and a
long thin tail ending in a spade tip, held away from the legs.
```

**Female:** `Female, about 175 cm tall, athletic build, slimmer horns.` ·
**Male:** `Male, about 188 cm tall, muscular build, large heavy horns.`

**Runen (höllische Siegel, Farbe Höllisches Magenta `infernal magenta`):**

- Zeichen: Schutz `a horned circle sigil` · Kraft `a flame` · Weg `a burning footprint` · Emblem `a horned crown above a burning eye` · Mut `a flaming sword` · Ausdauer `an unbroken chain` · Ruhm `a pair of bat wings`

- Stufe 1: `No runes on the body.`
- Stufe 2: `One small, elegant ornamental band around each forearm, inked into the skin: sharp hooked infernal scrollwork with the protection rune, {protection}, woven in as its centerpiece, infernal sigils with sharp hooks, and a small sign of courage, {courage}, on the back of each hand; dark lines, not glowing. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 3: `Elegant ornaments inked into the skin, sharp hooked infernal scrollwork: a band around each forearm with the protection rune, {protection}, as its centerpiece, and a slender vertical ornament on the outside of each lower leg with the journey rune, {journey}, at its center, a small sign of courage, {courage}, on the back of each hand, and a slender ornament on the outside of each thigh with the endurance rune, {endurance}; the lines glow faintly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`
- Stufe 4: `Elegant ornaments inked into the skin, sharp hooked infernal scrollwork: bands around both forearms with the protection rune, {protection}, an armband ornament around each upper arm with the strength rune, {strength}, a slender ornament on each lower leg with the journey rune, {journey}, and an ornate medallion between the shoulder blades, about the size of a hand, with {emblem} at its center, a small sign of courage, {courage}, on the back of each hand, a slender ornament on each outer thigh with {endurance}, and a small sign of glory, {glory}, on each shoulder blade beside the medallion; the lines glow brightly {color}. A beautiful, well-designed fantasy tattoo, most of the skin stays bare.`

**Negativ zusätzlich:** `fire, flames, smoke, wings`

### Fey

> **Stand November 2026:** Fey sind edle Waldfeen (Wunsch des Nutzers, Vorbild: schöne Fee mit schillernden Flügeln): klares elfisches Gesicht mit glatter Haut, keine Maske, kein Fell oder Flaum, keine Fühler; eng anliegendes Mieder aus Blättern und Blütenblättern (Moosgrün, Creme, Gold, Zartrosa); große durchscheinende Flügel halb geöffnet nach hinten. Maßgeblich sind die Prompts in `scripts/prompts/Fey/`; der Text unten ist der alte Entwurf.

```text
Fey, small and delicate, very slender petite build, pale lilac-tinted skin with a soft shimmer, large violet
eyes, long thin pointed ears. Signature: two pairs of small semi-opaque iridescent wings on the back, folded close
to the back and no wider than the shoulders, so they do not cover the body.
```

**Female:** `Female, about 140 cm tall, butterfly-like wings.` ·
**Male:** `Male, about 145 cm tall, dragonfly-like wings.`

**Wachstum statt Runen (Flügelmuster, Farbe):**

- Stufe 1: `Small folded wings with clear bright colors.`
- Stufe 2: `The small wings show more vivid colors. The lilac skin turns a softer, paler lilac.`
- Stufe 3: `The small wings show shimmering iridescent patterns and faint sparkling edges. The skin is a pale, delicate lavender with a light shimmer.`
- Stufe 4: `The small wings show rich iridescent patterns and softly glowing pink-violet edges; a faint shimmer on the skin. The skin is an airy pale silvery lavender, almost white, with a faint light shimmer.`

**Negativ zusätzlich:** `child, large wings, spread wings, wings covering the body, transparent wings, flying, floating, glitter particles`

### Stoneborn

```text
Stoneborn, living stone humanoid, heavy build, body made of gray granite with visible rock texture and plates,
smooth stone head, no ears, glowing amber eyes. Signature: amber crystal growths on the shoulders and forearms.
```

**Female:** `Female, about 210 cm tall, tall and heavy, smaller crystals.` ·
**Male:** `Male, about 230 cm tall, very tall and massive, broad shoulders, larger crystals.`

**Wachstum statt Runen (Kristalle und Adern, Farbe):**

- Stufe 1: `Small amber crystal growths on the shoulders and forearms.`
- Stufe 2: `The crystals are a little larger and faint amber veins appear between the stone plates. The gray granite turns a darker gray with a few amber flecks.`
- Stufe 3: `Larger amber crystals on the shoulders, forearms and back, glowing amber veins between the stone plates on arms and chest. The stone is dark gray basalt with many small amber flecks.`
- Stufe 4: `Large brightly glowing amber crystals on the shoulders, forearms and along the spine, bright amber veins over the whole body. The stone is a polished near-black like obsidian, with amber flecks and veins.`

**Negativ zusätzlich:** `human skin, lava, fire`

### Plantfolk

```text
Plantfolk, plant humanoid, skin of bark, glowing green eyes, root-like fingers and toes, small leaves on the
shoulders. Signature: leaves growing from the head like a crown instead of hair.
```

**Female:** `Female, about 175 cm tall, slender build, smooth light-brown bark.` ·
**Male:** `Male, about 185 cm tall, sturdy build, rough brown bark, small branches in the leaf crown.`

**Wachstum statt Runen (Blätter und Blüten, Farbe):**

- Stufe 1: `A crown of fresh young green leaves, no blossoms.`
- Stufe 2: `A fuller leaf crown with a few small white blossoms. The leaves turn a more vivid green and the bark a warmer brown.`
- Stufe 3: `A lush leaf crown with white blossoms, thin vines growing along the arms, a faint green glow in the bark cracks. The leaves are a strong saturated green, the bark a warm red-brown, the blossoms bright.`
- Stufe 4: `A magnificent crown of leaves and blooming white and golden flowers, vines with small leaves along the arms and legs, softly glowing sap-green lines in the bark. The leaves are an intense vivid emerald green, the bark a rich red-brown, the blossoms bright white and gold.`

**Negativ zusätzlich:** `human skin, flowers covering the body`

## Ansichten

Jede Ansicht ist ein **eigenes Bild** mit eigenem Aufruf des Bildgenerators. Nie mehrere Ansichten in einem Bild
anfordern und nie ein Bild in Teile schneiden. Erzeugt werden nur drei Bilder pro Set: `01_Front`, `02_Ruecken`
und `03_Links` (Figur schaut nach links im Bild). Der Prompt für `03_Links` verlangt das Profil mit der Nase zum
**rechten** Bildrand, weil Qwen-Image-Edit „facing left“ aus Sicht der Figur versteht und im Test so zeichnete;
`generate_references_local.py` spiegelt das Bild beim Speichern, sodass in `03_Links.jpg` die Nase zum linken
Bildrand zeigt. Wer den Prompt von Hand in einem anderen Generator nutzt, spiegelt das Bild ebenso. `04_Rechts` ist `03_Links` horizontal gespiegelt
und wird nicht gespeichert; `python Tools/Characters/make_right_views.py` erzeugt die rechten Ansichten lokal, wenn
man sie braucht (z. B. für Tripo). Das spart Zeit und Speicher, und die beiden Seiten passen genau zusammen.

**01_Front**
```text
Front view, facing the camera directly, looking straight ahead.
```

**02_Ruecken**
```text
Back view for a 3D modeling reference, seen directly from behind at chest height, same neutral A-pose, back of
the head visible.
```

**03_Links**
```text
Exact 90 degree side profile for a 3D modeling reference: the character has turned to their own left, so the
nose points to the right edge of the image. Only one eye is visible; shoulders and hips are seen edge-on, so
neither the chest nor the back faces the camera. Same pose, arms hanging at the sides.
```

**04_Rechts**: wird nicht erzeugt und nicht gespeichert, sondern bei Bedarf aus `03_Links` gespiegelt (siehe oben).

## Beispiel: HighElf Female, Body1 (Athletisch), Stufe 1 (`Stage1`), Front

So steht er auch in `Prompts/HighElf/Female_Body1_Stage1.md`.

```text
One young adult woman: a female High Elf character with a clearly feminine face and figure: a modest smooth bust without any detail, a slightly narrower waist and slightly wider hips than a man of her race.
High Elf, tall, slender and elongated proportions: long neck, long arms and legs, very little muscle mass, elegant and ethereal, clearly not human. Flawless pale porcelain skin with a faint pearlescent golden sheen, luminous golden eyes, thin fine pale eyebrows, refined angular face with high sharp cheekbones and a narrow chin, large almond-shaped eyes. Signature: long slender swept-back pointed ears that rise above the top of the head.
Female, about 185 cm tall, narrow shoulders, narrow waist, slim willowy figure, small bust.
Appearance variant: balanced. Athletic, well-proportioned build typical of the race; oval face with balanced features, medium straight nose, almond-shaped eyes. These differences override the build described above; the height and features of the race stay.
About 22 years old for their kind, youthful face with smooth skin, a fresh adventurer, natural relaxed upright posture.
No runes on the body.
High-quality realistic character render of a fantasy RPG character, in the style of a modern AAA game made in Unreal Engine 5 with scanned, lifelike humans: realistic skin with visible pores, fine surface detail and subtle natural color variation, natural subsurface scattering, sharp focus, high detail; not plastic, not clay, not a doll. Full body, standing straight in a relaxed A-pose, arms slightly away from the body, feet shoulder-width apart, barefoot. Bald head with no hair, no beard; the ears exactly as described for the race above, and species features such as fur, feathers, scales or horns stay. No clothing: the default base body of a game character creator, with the female or male body shape and muscles described above; chest and hips simplified and smooth, with no nipples and no genitals; fur, scales, feathers, stone or bark cover the body where the race has them. No jewelry, no weapons. Neutral calm expression, mouth closed. Plain neutral light gray studio background, soft even diffuse studio lighting, no rim light, no shadows on the background. Camera at chest height with a long lens, almost no perspective distortion. The whole figure is centered and fully in frame from the top of the head to the toes, including any tail, wings or horns, with a little space above and below. Portrait format 2:3. One single image showing one single character from one single camera angle; not a character sheet, not a turnaround, not a collage.
Front view, facing the camera directly, looking straight ahead.
```
