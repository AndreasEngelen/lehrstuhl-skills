# Lehrstuhl Skills – Chair Reviewer

Claude skills that give researchers structured, stage-adaptive feedback on paper sections at the standard of the Chair of Management (HHU Düsseldorf).

| Skill | What it reviews |
|---|---|
| `chair-introduction-reviewer` | The Introduction: gap/tension, why it matters, research question, central argument, contributions, proportionality |
| `chair-methods-reviewer` | The Methods section: sample waterfall, measures, control variables, estimation approach, leanness and length |

Both skills first ask which stage your draft is in (BLUE = early draft, YELLOW = mid-stage, GREEN = final refinement, WHITE = not sure) and adapt the depth of the review accordingly. They answer in the language you write in.

**Deutsch:** Eine deutsche Anleitung steht weiter unten.

## Manuals

| Manual | Language | What it covers |
|---|---|---|
| [`Manual_Introduction_schreiben.docx`](manuals/Manual_Introduction_schreiben.docx) | German | What a strong Introduction looks like at Chair standard: architecture, gap, research question, central argument, contributions, length, style, self-tests, checklist, and annotated passages from eight published Chair papers |

---

## Option A – Claude app (claude.ai, desktop, mobile)

1. Download the ZIP for the skill you want from the [`downloads`](downloads) folder (click the file, then the download button):
   - [`chair-introduction-reviewer.zip`](downloads/chair-introduction-reviewer.zip)
   - [`chair-methods-reviewer.zip`](downloads/chair-methods-reviewer.zip)
2. In Claude, open **Settings** and go to the section where you manage skills, then upload the ZIP. Do not unzip it.
3. Start a new chat and write, for example: *"Please review the Methods section of my paper"* and attach your draft (Word, PDF, or pasted text).

**Updates:** Skills uploaded this way do not update themselves. Check the [changelog](#changelog) below; if there is a newer version, download the ZIP again and replace the old skill.

## Option B – Claude Code

Run these two commands once in Claude Code:

```
/plugin marketplace add AndreasEngelen/lehrstuhl-skills
/plugin install chair-reviewer@lehrstuhl-skills
```

To pull new versions, run `/plugin marketplace update lehrstuhl-skills` (or enable auto-update for the marketplace in `/plugin`).

---

## Deutsch

**Claude-App (claude.ai, Desktop, Mobil)**

1. Lade im Ordner [`downloads`](downloads) die ZIP-Datei des gewünschten Skills herunter.
2. Öffne in Claude die **Einstellungen**, gehe zum Bereich für Skills und lade die ZIP-Datei hoch. Die Datei dabei nicht entpacken.
3. Starte einen neuen Chat, zum Beispiel mit *„Bitte reviewe den Methods-Teil meines Papers“*, und hänge deinen Entwurf an.

Updates kommen bei diesem Weg nicht automatisch. Schau ins Changelog unten und lade bei einer neuen Version die ZIP-Datei erneut hoch.

**Claude Code:** siehe Option B oben.

**Manual:** Im Ordner [`manuals`](manuals) liegt das Word-Manual [„Die Introduction schreiben“](manuals/Manual_Introduction_schreiben.docx). Es beschreibt, wie eine Introduction auf Lehrstuhl-Niveau aussieht, mit Selbsttests, Checkliste und kommentierten Passagen aus acht publizierten Lehrstuhl-Papern.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-09-27 | First release: Introduction reviewer and Methods reviewer |
| 1.0.1 | 2026-09-27 | Added the German manual "Die Introduction schreiben" (Word) |
