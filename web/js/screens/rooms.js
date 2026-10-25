import { h, STATUS_LABEL } from "../dom.js";

/**
 * @param {{hostel_name: string, round_label: string, progress: {done: number, total: number},
 *          rooms: {room_id: string, serial_last4: string|null, status: string}[]}} round
 * @param {(roomId: string) => void} openRoom
 */
export function roomsScreen(round, openRoom) {
  const { done, total } = round.progress;
  const percent = total ? Math.round((done / total) * 100) : 0;
  return h("section", {},
    h("header", { class: "header" },
      h("h1", {}, `${round.hostel_name} · Meter round · ${round.round_label}`),
    ),
    h("div", { class: "progress" },
      h("p", {}, h("strong", {}, `${done} / ${total}`), " rooms ho gaye"),
      h("div", { class: "bar", role: "progressbar", "aria-valuenow": done, "aria-valuemin": 0, "aria-valuemax": total },
        h("span", { style: `width:${percent}%` })),
    ),
    h("ul", { class: "rooms" },
      ...round.rooms.map((room) => h("li", {},
        h("button", { class: "room-row", onClick: () => openRoom(room.room_id) },
          h("span", {},
            h("span", { class: "name" }, `Room ${room.room_id}`),
            room.serial_last4 ? h("span", { class: "serial mono" }, `  …${room.serial_last4}`) : null,
          ),
          h("span", { class: `chip ${room.status}` }, STATUS_LABEL[room.status] ?? room.status),
        ),
      )),
    ),
  );
}
