import { h, shortDate } from "../dom.js";

/**
 * @param {{room_id: string, serial: string|null, serial_last4: string|null,
 *          previous_reading: string|null, previous_at: string|null, status: string, hint: string}} room
 * @param {{back: () => void, takePhoto: () => void}} actions
 */
export function roomScreen(room, actions) {
  const needsMeter = !room.serial;
  const serialLine = needsMeter
    ? h("p", {}, "Is room ka meter abhi juda nahi hai.")
    : h("p", { class: "serial-line mono" },
        `Meter SN-${room.serial.slice(0, -4)}`,
        h("span", { class: "tail" }, room.serial_last4));
  const previous = needsMeter ? null : h("div", { class: "previous" },
    h("span", {}, "Pichhli reading"),
    room.previous_reading
      ? h("span", { class: "value mono" }, room.previous_reading,
          h("span", { class: "sub" }, room.previous_at ? `  · ${shortDate(room.previous_at)}` : ""))
      : h("span", {}, "Abhi baseline nahi hai"),
  );
  return [
    h("section", { class: "room-screen" },
      h("button", { class: "back", onClick: actions.back }, "‹ Rooms"),
      h("h2", {}, `Room ${room.room_id}`),
      serialLine,
      previous,
      h("p", { class: "hint" }, room.hint),
    ),
    h("div", { class: "action-bar" },
      h("button", { class: "button", onClick: actions.takePhoto },
        needsMeter ? "Meter ki photo lo" : "Photo lo")),
  ];
}
