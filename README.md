# Lehrstuhl Skills – Chair Reviewer

Claude skills that give researchers structured, stage-adaptive feedback on paper sections at the standard of the Chair of Management (HHU Düsseldorf).

| Skill | What it reviews |
|---|---|
| `chair-introduction-reviewer` | The Introduction: gap/tension, why it matters, research question, central argument, contributions, proportionality |
| `chair-methods-reviewer` | The Methods section: sample waterfall, measures, control variables, estimation approach, leanness and length |
| `chair-findings-reviewer` | The Findings section: verdicts for every hypothesis, test–hypothesis fit (probing, indirect effects, formal comparisons), effect sizes, robustness checks, additional analyses, leanness and length |
| `chair-discussion-reviewer` | The Discussion: opening summary, theoretical implications that mirror the Introduction's contributions, interpretation of unexpected findings, limitations and future research, practical implications, length |

All skills first ask which stage your draft is in (BLUE = early draft, YELLOW = mid-stage, GREEN = final refinement, WHITE = not sure) and adapt the depth of the review accordingly. They answer in the language you write in.

**Deutsch:** Eine deutsche Anleitung steht weiter unten.

## Manuals

| Manual | Language | What it covers |
|---|---|---|
| [`Manual_Introduction_schreiben.pdf`](manuals/Manual_Introduction_schreiben.pdf) | German | What a strong Introduction looks like at Chair standard: architecture, gap, research question, central argument, contributions, length, style, self-tests, checklist, and annotated passages from eight published Chair papers |
| [`Manual_Methodenteil_schreiben.pdf`](manuals/Manual_Methodenteil_schreiben.pdf) | German | What a strong Methods section looks like at Chair standard: the five Chair rules, sample waterfall, measures (incl. new-measure validation), control variables, estimation, leanness, length benchmark, self-tests, checklist, and annotated passages from eight published Chair papers |
| [`Manual_Ergebnisteil_schreiben.pdf`](manuals/Manual_Ergebnisteil_schreiben.pdf) | German | What a strong Findings section looks like at Chair standard: the six Chair rules, calibrated verdicts, moderation and mediation, effect sizes, robustness checks, additional analyses, fsQCA findings, length benchmark, self-tests, checklist, and annotated passages from nine published Chair papers |
| [`Manual_Discussion_schreiben.pdf`](manuals/Manual_Discussion_schreiben.pdf) | German | What a strong Discussion looks like at Chair standard: the seven Chair rules, contributions that mirror the Introduction, interpreting unexpected findings, calibration, limitations and future research, practical implications, length benchmark, self-tests, checklist, and annotated passages from eleven published Chair papers |

---

## Option A – Claude app (claude.ai, desktop, mobile)

1. Download the ZIP for the skill you want from the [`downloads`](downloads) folder (click the file, then the download button):
   - [`chair-introduction-reviewer.zip`](downloads/chair-introduction-reviewer.zip)
   - [`chair-methods-reviewer.zip`](downloads/chair-methods-reviewer.zip)
   - [`chair-findings-reviewer.zip`](downloads/chair-findings-reviewer.zip)
   - [`chair-discussion-reviewer.zip`](downloads/chair-discussion-reviewer.zip)
2. In Claude, open **Settings** and go to the section where you manage skills, then upload the ZIP. Do not unzip it.
3. Start a new chat and write, for example: *"Please review the Methods section of my paper"* and attach your draft (Word, PDF, or pasted text).

**Updates:** Skills uploaded this way do not update themselves. Check the [changelog](#changelog) below; if there is a newer version, download the ZIP again and replace the old skill.

## Option B – Claude Code

Run these two commands once in Claude Code:

```
/plugin marketplace add AndreasEngelen/lehrstuhl-skills
/plugin install chair-reviewer@lehrstuhl-skills
```

**Updates:** Auto-update is off by default for this marketplace. To get new skills and versions:

- once: run `claude plugin update chair-reviewer@lehrstuhl-skills` in your terminal (or in Claude Code: `/plugin` → **Installed** → `chair-reviewer` → **Update now**), then `/reload-plugins` or start a new session;
- automatically from now on: `/plugin` → **Marketplaces** → `lehrstuhl-skills` → **Enable auto-update**.

---

## Deutsch

**Claude-App (claude.ai, Desktop, Mobil)**

1. Lade im Ordner [`downloads`](downloads) die ZIP-Datei des gewünschten Skills herunter.
2. Öffne in Claude die **Einstellungen**, gehe zum Bereich für Skills und lade die ZIP-Datei hoch. Die Datei dabei nicht entpacken.
3. Starte einen neuen Chat, zum Beispiel mit *„Bitte reviewe den Methods-Teil meines Papers“*, und hänge deinen Entwurf an.

Updates kommen bei diesem Weg nicht automatisch. Schau ins Changelog unten und lade bei einer neuen Version die ZIP-Datei erneut hoch.

**Claude Code:** siehe Option B oben. Updates kommen dort nur automatisch, wenn du in `/plugin` → **Marketplaces** → `lehrstuhl-skills` **Enable auto-update** wählst; sonst einmalig `claude plugin update chair-reviewer@lehrstuhl-skills` ausführen.

**Manual:** Im Ordner [`manuals`](manuals) liegen vier Manuals als PDF: [„Die Introduction schreiben“](manuals/Manual_Introduction_schreiben.pdf), [„Den Methodenteil schreiben“](manuals/Manual_Methodenteil_schreiben.pdf), [„Den Ergebnisteil schreiben“](manuals/Manual_Ergebnisteil_schreiben.pdf) und [„Die Discussion schreiben“](manuals/Manual_Discussion_schreiben.pdf). Sie beschreiben, wie der jeweilige Teil auf Lehrstuhl-Niveau aussieht, mit Selbsttests, Checkliste und kommentierten Passagen aus publizierten Lehrstuhl-Papern.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-09-27 | First release: Introduction reviewer and Methods reviewer |
| 1.0.1 | 2026-09-27 | Added the German manuals "Die Introduction schreiben" and "Den Methodenteil schreiben" (PDF) |
| 1.1.0 | 2026-09-27 | Added the Findings reviewer (`chair-findings-reviewer`) and the German manual "Den Ergebnisteil schreiben" (PDF) |
| 1.2.0 | 2026-09-27 | Added the Discussion reviewer (`chair-discussion-reviewer`) and the German manual "Die Discussion schreiben" (PDF); clarified how Claude Code users get updates |
