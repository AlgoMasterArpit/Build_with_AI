---
doc: prd
status: approved
---

# MeterMind — Product Requirements

A phone-browser meter round for a hostel caretaker: photograph each room's meter, and an agent checks the photo, catches the wrong meter, re-reads unclear digits, and either saves the reading or sends the room to review.
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`.

## The Core Journey

Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. The admin sends the caretaker one link on WhatsApp: "Hostel A · Meter round". The link carries a secret token that identifies the caretaker and the hostel. No login or password.
2. If the link opened inside WhatsApp's in-app browser, the first screen says "Ye link Chrome mein kholo" with a **Chrome mein kholo** button.
3. The caretaker sees the **Rooms List** for this month's round and taps Room 205.
4. The **Room Screen** shows the room, its meter serial and previous reading, a one-line hint, and a **Photo lo** button.
5. Tapping **Photo lo** opens the full-screen camera with a frame guide. On first use the browser asks for camera permission, then location permission.
6. The caretaker takes a live photo. The agent checks it and responds in a one-line instruction strip under the photo:
   - Bad photo (glare, blur, darkness): the problem area is marked in red on the photo and the strip says exactly what to change, e.g. "Upar right mein glare hai, phone thoda left tilt karo." The caretaker retakes.
   - Wrong meter (serial does not match Room 205): "Ye Room 205 ka meter nahi hai, board pe …4821 dhoondho." The caretaker retakes.
   - Right meter: the display is shown straightened with a box and confidence on every digit. An unclear digit shows yellow and the strip says it is being re-read; after the re-read it turns green.
7. Success: green tick, light vibration, "Reading save" with units since the previous reading and CO₂, and an **Agent ne kya kiya** step list (e.g. glare → retake → wrong meter caught → right meter → digit re-read → save). The room turns green in the list and the caretaker moves to the next room.
8. If the agent reaches a limit (see **Agent Limits and Review**), an orange card sends the room to review and the caretaker moves on. The caretaker is never stuck.

## Screens and Layout

1. **Open-in-Chrome notice** — only when the link opens in WhatsApp's in-app browser.
2. **Rooms List**
   - Header: "Hostel A · Meter round · Oct 2026"
   - Progress: "3 / 12 rooms ho gaye"
   - One row per room: room number, last 4 digits of the meter serial, status.
3. **Room Screen** (before the camera)
   - Large heading: "Room 205"
   - "Meter SN-…4821": full serial small, last 4 digits large, so the caretaker can find the right meter on the board.
   - "Pichhli reading: 01910 · 21 Oct", or "Abhi baseline nahi hai" for a new meter.
   - Hint: "Meter ka display aur serial number dono frame mein rakho."
   - Bottom button: **Photo lo**.
4. **Camera** — full screen, always dark, frame guide for the display and serial.
5. **Result** — the photo with boxes and highlights, the one-line instruction strip, and the next action (retake, or continue).
6. **Saved card** — green tick, reading, units, CO₂, Agent ne kya kiya.
7. **Review card** — orange, see **Agent Limits and Review**.
8. **Add Meter Screen** and **Add Meter Confirm** — see **Add Meter**.
9. **Camera Blocked card** — see **Permissions**.

Movement: Rooms List → Room Screen or Add Meter Screen → Camera → Result → Saved or Review card → back to Rooms List.

## Look and Feel

- A work tool, not an AI app: "jaise caretaker ka register digital ho gaya ho, aur saath mein koi samajhdaar senior khada ho jo ek line mein bata de ki kya karna hai."
- Follows the phone's light/dark setting, both designed properly. The camera screen is always dark and full screen so the meter photo is the brightest thing.
- Neutral base (off-white, or deep slate in dark). One accent: water blue, for buttons and links only.
- Fixed status colours, used nowhere else: green = Ho gaya, orange = Review mein, grey = Baaki, and Meter jodna hai as a light-blue outline-only chip, a different shade from the button accent. Red appears only on top of the photo, where glare or a problem is.
- Readings and serials in a monospace, equal-width font (IBM Plex Mono or JetBrains Mono); the reading is the largest thing on screen, about 40px or more. Other text in a clean, slightly industrial sans (IBM Plex Sans), at least 16–18px. No small grey text.
- One-handed: the main button is always at the bottom, full width, within thumb reach.
- Digit boxes look like Google Lens text boxes. The agent speaks in a single-line strip under the photo: no chat bubbles, no robot icon, no "AI soch raha hai…".
- On save: light vibration and a green tick, nothing more.
- References: GPay/PhonePe QR scanner (opens straight to the camera, frame, done) and the Uber driver app (big buttons, readable at a glance).
- Never: purple or neon gradients, sparkle icons, glassmorphism, chat interface, confetti, emojis, charts or graphs on the caretaker's screens, long paragraphs. If something doesn't fit in one line, it belongs in the report, not on the caretaker's screen.

## Features and Behavior

### Meter Round Link

- One link per caretaker and hostel, carrying a secret token; no login.
- [ ] Opening the link shows that hostel's Rooms List for the current round.
- [ ] Opening it inside WhatsApp's in-app browser shows the Open-in-Chrome notice instead.

### Rooms List

- [ ] Every room shows its number, last 4 serial digits and one status: Baaki (grey), Ho gaya (green), Review mein (orange), Meter jodna hai (light-blue outline chip).
- [ ] Progress shows rooms done out of total.
- [ ] Tapping a room with a meter opens the Room Screen; tapping a "Meter jodna hai" room opens the Add Meter Screen.
- [ ] A room in Review mein can be opened again for another attempt; each opening starts with fresh attempt limits.
- [ ] Tapping a Ho gaya room shows its Saved card (reading, units, Agent ne kya kiya) with no option to take another photo, so a room never gets two readings in one month.

### Live Capture Only

Source: `scope.md > Explicitly Cut` (gallery upload).

- [ ] The only way to submit a reading is a photo taken in the in-app camera. There is no gallery upload and no box to type a reading or serial.
- [ ] The previous month's photo is never shown.
- [ ] Every photo is stored with the server's time; location is attached when available.

### Photo Quality Check

- [ ] Glare, blur and darkness are detected; the problem area is marked in red on the photo.
- [ ] The strip gives one specific instruction for what to change.

### Right-Meter Check

- [ ] The agent reads the serial from the photo and compares it with the room's registered meter.
- [ ] On mismatch the strip says "Ye Room 205 ka meter nahi hai, board pe …4821 dhoondho."

### Reading the Display

- [ ] The display is shown straightened with a box and confidence on every digit.
- [ ] A digit below the confidence threshold shows yellow; the agent re-reads it with different processing and, if needed, asks for one new live photo.
- [ ] A re-read digit that becomes clear turns green.

### Saving a Reading

- [ ] On success: green tick, light vibration, the reading, units since the previous reading, and CO₂ when that meter type has an emission factor (water shows units only if no trustworthy factor is found).
- [ ] The Agent ne kya kiya list shows each step the agent took in order.
- [ ] The room turns green and progress goes up by one.
- [ ] If the new reading is lower than the previous one, no units are calculated and the room goes straight to review with the reason "Reading pichhli se kam hai."

### Agent Limits and Review

The agent always tries by itself first; each problem has a limit, and past it the room goes to review so the caretaker can move on.

| Problem | What the agent does | When it goes to review |
| --- | --- | --- |
| Bad photo (blur, glare, darkness) | Exact retake instruction each time | Still bad after 3 retakes |
| Unclear digit | Re-reads with different processing, then asks for one new live photo | Any digit still below the threshold after that |
| Wrong meter (serial mismatch) | "Ye Room 205 ka meter nahi hai, board pe …4821 dhoondho" | 2 mismatches in a row |
| Serial can't be read | "Serial number nahi padh paaye. Sticker ko frame ke beech mein lo, chamak se bachao." | Still unreadable after 3 tries |
| Reading lower than the previous one | Nothing (POC) | Immediately |

- [ ] The orange Review card names the room, gives a one-line reason (e.g. "Aakhri digit 3 koshish ke baad bhi saaf nahi hua."), says the reading was not saved, and offers **Agle room pe jao**. No units or bill are shown.
- [ ] A review case is saved as a record: status needs review, the one-line reason, all photos, and the full agent trace. There is no review screen in the POC; the record and trace are what the demo and report show.
- [ ] If a later attempt on that room succeeds, the room turns green and the earlier review stays in its trace.

### Add Meter

Source: `scope.md > The POC Boundary` (Add meter, baseline).

- Rooms come pre-filled; Add Meter only links a meter to an existing room.
- [ ] A room without a meter shows "Meter jodna hai" (light-blue outline chip). Tapping it opens: "Room 205", "Is room ka meter abhi juda nahi hai.", hint "Meter ka serial sticker aur display dono frame mein rakho.", button **Meter ki photo lo**.
- [ ] The same quality, glare and digit re-read rules apply.
- [ ] The confirm screen shows the photo with boxes on the serial sticker and display, "SN-…4821" large, "Pehli reading: 01910", the question "Ye meter Room 205 ka hai?", and two buttons: **Haan, jodo** and **Nahi, dobara photo lo**. Numbers can't be edited.
- [ ] **Haan, jodo** links the meter, saves the reading as the baseline, and turns the room green: "Meter juda · Baseline save". No units are shown for a baseline.
- [ ] If the serial can't be read: "Serial number nahi padh paaye. Sticker ko frame ke beech mein lo, chamak se bachao.", up to 3 times. No reading is saved without a serial. After 3 failures, an orange card: "Room 205 ka meter jod nahi paaye. Serial padha nahi gaya. Review ke liye bhej diya, aap agle room pe ja sakte ho."
- [ ] If the serial is already linked to another room: "Ye meter Room 204 se juda hai. Room 205 ka meter dhoondho." After 2 such attempts the room goes to review.

### Permissions

- [ ] Camera blocked: tapping **Photo lo** shows "Camera band hai / Meter ki photo ke liye camera chahiye." with Android Chrome steps (lock icon in the address bar → Permissions → Camera → Allow), a small screenshot, and a **Dobara try karo** button that re-checks and opens the camera once allowed.
- [ ] Location is requested right after camera permission is granted, never at the same time.
- [ ] Location denied, or not found within 5 seconds: the photo still works, the record notes "location: nahi mili (deny ya timeout)", and the screen shows one line: "Location band hai, photo phir bhi save hogi." No blocking popup, and missing location alone never sends a room to review.

## States and Boundaries

- **First use** — the browser asks for camera permission on the first **Photo lo**, then location.
- **New meter** — Room Screen shows "Abhi baseline nahi hai"; the first saved reading is a baseline with no units.
- **Normal use** — Rooms List shows progress; each room ends Ho gaya or Review mein.
- **Review** — orange card, reading not saved, room can be opened again later with fresh attempt limits.
- **Done room reopened** — the Saved card is shown again; no new photo.
- **New month** — every room starts as Baaki, including last month's review rooms; the previous reading stays the last SAVED or BASELINE one.
- **Camera blocked** — Camera Blocked card with steps and retry.
- **Location unavailable** — photo continues; one-line note.
- **WhatsApp in-app browser** — Open-in-Chrome notice.
- **What persists** — room statuses, saved readings, baselines, review records, photos and agent traces stay between visits; reopening the link shows the round where it was left.
- **Who can do what** — the caretaker can only photograph and confirm which room a meter belongs to; they can never type or edit a reading or serial.

## Product Decisions

- One link per caretaker and hostel, not per room — matches how a round actually works; rooms are picked from a list.
- No login in the POC — the secret token in the link identifies caretaker and hostel.
- No typed readings or serials anywhere — "reading sirf photo se aati hai, warna verify karne ka koi matlab nahi"; a mistyped serial would raise a false wrong-meter alarm every month.
- Previous month's photo is never shown — otherwise it could be copied and the serial check demo would weaken.
- The agent gives up at fixed limits and the caretaker moves on — "caretaker ko kabhi atakna nahi padta."
- "Review mein", not "Auditor ke paas" — the POC has no auditor screen, so don't promise one.
- Review cases are saved records with photos and trace, no review screen — the later auditor dashboard will read the same records.
- Backwards reading only blocks the units and sends to review — stops a wrong negative number without building the later jump/random-angle flow.
- Add Meter confirms only "is this meter in this room?" — the camera can't know which room, only the caretaker can; numbers stay untouched.
- One serial can belong to only one room.
- Camera is required, location is optional — identity comes from the serial; corridor GPS is weak; requiring it would block honest work.
- Permission steps cover Android Chrome only — assumed caretaker phone.

## What We're Building

- Meter round link with token, Open-in-Chrome notice
- Rooms List with statuses and progress
- Room Screen, full-screen Camera with frame guide, Result with digit boxes and instruction strip
- Photo quality check with red marking and specific retake instructions
- Right-meter check via serial
- Display straightening, per-digit confidence, automatic re-read and one extra live photo
- Saved card with units, CO₂ and Agent ne kya kiya
- Agent limits and Review card; review records with photos and trace; retry from the list
- Backwards-reading guard
- Add Meter flow with confirm, serial-read failures and already-linked guard
- Camera Blocked card and optional location
- Pre-filled rooms (seed), light and dark themes per **Look and Feel**

## Deferred From the POC

- Auditor/committee review screen with Approve/Reject — review records are saved now; the screen comes with the dashboard.
- Creating rooms or importing a consumer CSV — rooms are pre-filled for the POC.
- Sending the link automatically — the admin shares it by hand on WhatsApp.
- 10× jump flag and random-angle re-capture — not in the demo journey and costly for the POC.
- Permission help for iPhone and other browsers — Android Chrome is assumed.

## Possible Later Enhancements

- Resident link with photo proof, history and a "Ye galat hai" dispute.
- Room or flat bill split, and a main-meter gap check for leaks or theft.
- Old-photo reuse and edit-mark detection.
- WhatsApp or SMS delivery.
- COOL vs standard OpenCV benchmark on Graviton (OpenCV AI Competition version).
- MSME factory sub-meters for carbon reporting.

## Non-Goals

- No gallery upload and no typed readings or serials — they would defeat verification.
- No chat interface or AI persona — it's a work tool.
- No charts or graphs on the caretaker's screens — one-line rule.
- No claim of catching every forgery — the final decision stays with a human.
- No login, accounts or roles in the POC.

## Open Questions

- Resolved in spec: a wrong or expired token shows "Ye link sahi nahi hai, admin se naya link maango" (`spec.md > Round Link and Rooms API`).
- Resolved in spec: the admin creates the round link and pre-fills rooms with the seed script (`spec.md > Where It Runs and How Someone Tries It`).
- Which CO₂ factor applies to each meter type (electricity sub-meter in the demo, water, gas)? Can wait for `4-spec`.
- What is the digit confidence threshold? Decided during the build from real photos.
