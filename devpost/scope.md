---
doc: scope
status: approved
---

# MeterMind

An AI agent that reads a utility meter from a live phone photo, doubts the photo when something is off, and decides by itself what to do next.

## The Unique Kernel

A normal OCR app reads the number even when the photo is blurry or fake. MeterMind "ek samajhdaar insaan ki tarah sochta hai ki ye photo theek hai bhi ya nahi, aur agar nahi hai toh ab kya karna chahiye": it asks for a retake with a specific hint, catches the wrong meter, re-reads an unclear digit on its own, and shows a trace of what it did and why.

## Who It's For

A hostel caretaker who photographs every room's meter each month so each room is billed on its real use, not an average. Today readings are taken by hand or by eye, and nobody checks whether a photo shows the right meter or tells the truth.
The same flow serves utility meter readers and housing-society managers for water and gas meters, where there is no smart meter or data port and the photo is the only proof.

## The Core Loop

The caretaker opens the round link on the phone browser, picks Room 205 from the rooms list, takes a live photo (no gallery upload), and the agent either accepts the reading or tells them exactly what to fix. Then the next room. They come back every billing cycle.

## Inspiration & Identity

Grounded in real cases: a Pune society hit with a ₹24 lakh water bill after months without readings, average bills in Chandigarh, Delhi Jal Board requiring photo proof, and an Odisha meter reader who edited the reading and removed the meter number from a photo. It should feel like a careful colleague, not a scanner: clear instructions, visible reasoning.

## Why This Matters to the Learner

"Utilities ke paas har mahine lakhon photos aati hain aur unhe koi automatically verify nahi karta. Mujhe yahi gap sabse interesting laga." And: "Mere liye MeterMind ka matlab yahi hai ki meter ki reading pe phir se bharosa kiya ja sake."

## What "Working" Looks Like

A one-minute run in a hostel corridor with a row of meters:

1. The round link opens the rooms list; the caretaker taps Room 205 and sees its screen (serial, previous reading), then taps **Photo lo**.
2. First photo has glare: the glare area is highlighted and the agent says "Upar right mein glare hai, phone thoda left tilt karo."
3. The caretaker photographs Room 204's meter by mistake: the agent reads the serial and says "Ye Room 205 ka meter nahi hai, board pe …4821 dhoondho." This is the "oh, that's cool" beat.
4. The right meter: the display is straightened, every digit gets a box and confidence; one digit is unclear, the agent says it is re-reading, and the digit turns green.
5. Saved: units since the previous reading and CO₂ (for the demo's electricity sub-meter; water shows units only if no trustworthy factor is found), plus an "Agent ne kya kiya" trace: glare → retake → wrong meter caught → right meter → digit re-read → save.

## The POC Boundary

- One round link with a rooms list; live-camera-only capture from the phone browser
- Photo quality check (glare, blur, darkness) with a specific retake instruction
- Serial-number check against the room's registered meter
- Display straightening, digit reading with per-digit confidence, automatic re-read of unclear digits
- Save the reading with units since the previous reading and CO₂, and show the agent trace
- Pre-filled room list via a seed script, plus a small "Add meter" flow: pick a room, photograph the meter, serial and first (baseline) reading saved; the first month shows "Baseline save", not units
- Agent limits and review: each problem has a limit; past it the room goes to "Review mein", saved as a record (no review screen). The LLM picks the next step, the code enforces the limits, and rules take over if the LLM fails
- Backwards-reading guard: a reading lower than the previous one shows no units and goes straight to review
- Rooms 204 and 205 registered through Add meter from real photos on 2026-10-26 (around 13:00–15:00 IST), a few hours before the evening shoot; no invented previous readings (units will be small; the video says "pichhli reading se ab tak", not "is mahine")

## Later

- Resident link with photo proof, history graph and "Ye galat hai" dispute
- Room/flat bill split and main-meter gap (leak/theft) check
- Auditor or committee dashboard to approve or reject flagged cases
- Old-photo reuse detection (image hash + ORB), edit-mark detection, random-instruction live re-capture
- 10× jump or backwards-reading flags (POC has only the backwards guard, with no new flow)
- CSV import of an existing consumer list
- WhatsApp or SMS delivery
- COOL vs standard OpenCV benchmark on Graviton (OpenCV AI Competition version)
- MSME factory sub-meters for carbon reporting

## Explicitly Cut

- Gallery upload: removed on purpose, live photos only, so an edited image has no normal way in.
- Electricity as the headline: smart meters and probe reading are replacing photo readings there; electricity LCD meters stay as a fallback for the demo only.
- A claim of catching every forgery: a good forgery can't be caught from pixels alone, so the final decision stays with a human.
