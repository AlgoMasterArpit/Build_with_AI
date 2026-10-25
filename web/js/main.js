import { api, ApiError, token } from "./api.js";
import { h, render } from "./dom.js";
import { roomScreen } from "./screens/room.js";
import { roomsScreen } from "./screens/rooms.js";

const app = /** @type {HTMLElement} */ (document.getElementById("app"));

function notice(title, message, action) {
  render(app, h("section", { class: "notice" },
    h("h1", {}, title),
    h("p", {}, message),
    action ? h("button", { class: "button", onClick: action.run }, action.label) : null));
}

function failed(error) {
  if (error instanceof ApiError && error.code === "invalid_link") {
    notice("Link kaam nahi kar raha", error.message);
  } else {
    notice("Kuch gadbad hui", error.message ?? String(error),
      { label: "Dobara try karo", run: () => route() });
  }
}

async function showRooms() {
  const round = await api("/round");
  render(app, roomsScreen(round, (roomId) => { location.hash = `#/room/${roomId}`; }));
}

async function showRoom(roomId) {
  const room = await api(`/rooms/${encodeURIComponent(roomId)}`);
  render(app, ...roomScreen(room, {
    back: () => { location.hash = "#/rooms"; },
    takePhoto: () => { location.hash = `#/camera/${roomId}`; },
  }));
}

const routes = [
  [/^#\/room\/([^/]+)$/, showRoom],
  [/^(#\/rooms)?$/, showRooms],
];

async function route() {
  if (!token) {
    notice("Link kaam nahi kar raha", "Ye link sahi nahi hai, admin se naya link maango.");
    return;
  }
  const hash = location.hash;
  const match = routes.find(([pattern]) => pattern.test(hash));
  if (!match) {
    location.hash = "#/rooms";
    return;
  }
  render(app, h("p", { class: "loading" }, "Load ho raha hai…"));
  try {
    await match[1](...hash.match(match[0]).slice(1).map(decodeURIComponent));
  } catch (error) {
    failed(error);
  }
}

window.addEventListener("hashchange", route);
route();
