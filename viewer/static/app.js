// Traffic signs viewer: one row per sign, one column per country.
// Data comes from data.json (built by `python3 -m viewer`).

const PAGE_SIZE = 100; // signs added to the page at a time, as the reader scrolls

const state = { query: "", category: "", group: "", countries: new Set(), shared: false, withdrawn: true, sort: "" };

// Orders of the signs within each type; "" keeps the order of data.json.
const SORTS = {
  "": "Default order",
  "countries-desc": "Most countries first",
  "countries-asc": "Fewest countries first",
  name: "Name A–Z",
};
let data;
const signsByKey = new Map(); // "warning/crosswind" -> sign
// What render() matched, in display order, and how much of it is on the page.
const view = { signs: [], columns: [], shown: 0, groups: new Map() };

const $ = (id) => document.getElementById(id);

// Sharing: links point at share/… pages (built by `python3 -m viewer`), which
// carry the title, description and picture that link previews show, and send
// the visitor on to the sign or category here.
const SITE = new URL(".", location.href);
const signLink = (sign) => new URL(`share/${sign.category}/${sign.sign}/`, SITE).href;
const categoryLink = (category) => new URL(`share/${category}/`, SITE).href;

async function share(url, title) {
  try {
    if (navigator.share) {
      await navigator.share({ title, url });
      return;
    }
    await navigator.clipboard.writeText(url);
    toast("Link copied");
  } catch (error) {
    if (error?.name === "AbortError") return; // the share sheet was closed
    window.prompt("Copy this link:", url);
  }
}

function toast(text) {
  const note = $("toast");
  note.textContent = text;
  note.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (note.hidden = true), 2000);
}

function shareButton(label, url, title) {
  const button = el("button", { type: "button", class: "share", title: label, "aria-label": label }, "Share");
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    share(url, title);
  });
  return button;
}

// The filters live in the URL (?type=warning&q=bend&countries=sk,cz&shared=1&sort=name),
// so a filtered list can be bookmarked or shared as it is.
function readUrl() {
  const params = new URLSearchParams(location.search);
  if (params.get("type") in data.categories) state.category = params.get("type");
  state.query = (params.get("q") || "").trim();
  state.shared = params.get("shared") === "1";
  state.withdrawn = params.get("withdrawn") !== "0";
  state.sort = params.get("sort") in SORTS ? params.get("sort") : "";
  const wanted = (params.get("countries") || "").split(",").filter((c) => c in data.countries);
  const group = groupById(params.get("group"));
  if (group?.countries.length) {
    state.group = group.id;
    state.countries = new Set(group.countries);
  } else {
    state.countries = new Set(wanted.length ? wanted : nationals());
  }
}

function writeUrl() {
  const params = new URLSearchParams();
  if (state.category) params.set("type", state.category);
  if (state.query) params.set("q", state.query);
  if (state.group) params.set("group", state.group);
  else if (!allCountries()) params.set("countries", [...state.countries].join(","));
  if (state.shared) params.set("shared", "1");
  if (!state.withdrawn) params.set("withdrawn", "0");
  if (state.sort) params.set("sort", state.sort);
  const search = params.toString().replace(/%2C/g, ",");
  const url = location.pathname + (search ? `?${search}` : "") + location.hash;
  if (url !== location.pathname + location.search + location.hash) history.replaceState(history.state, "", url);
}

// The filters as a first visit has them; "Reset filters" goes back to these.
const isDefault = () =>
  !state.query && !state.category && !state.group && !state.shared && state.withdrawn && !state.sort && allCountries();

function resetFilters() {
  Object.assign(state, { query: "", category: "", group: "", countries: new Set(nationals()), shared: false, withdrawn: true, sort: "" });
  $("search").value = "";
  $("sort").value = "";
  $("group").value = "";
  $("shared").checked = false;
  $("withdrawn").checked = true;
  syncChips();
  render();
}

// The country checkboxes and the Countries menu follow state.countries.
function syncChips() {
  for (const box of $("countries").querySelectorAll("input")) box.checked = state.countries.has(box.value);
  if (!state.group) $("group").value = allCountries() ? "" : "custom";
}

// Change the chosen countries by hand (the buttons and checkboxes): that leaves
// any group, and the menu shows "Chosen countries".
function chooseCountries(update) {
  update(state.countries);
  state.group = "";
  syncChips();
  render();
}

const groupById = (id) => (data.groups || []).find((g) => g.id === id);

// The "Countries" menu: all countries, continents, then political and economic
// groups. A group selects the countries it has signs for; one without any yet
// is listed but cannot be chosen.
function setupGroups() {
  const select = $("group");
  const option = (g) => {
    const label = `${g.label} (${g.countries.length}${g.countries.length < g.members ? ` of ${g.members}` : ""})`;
    return el("option", { value: g.id, disabled: !g.countries.length }, label);
  };
  const kinds = [
    ["continent", "Continents"],
    ["group", "Groups"],
    ["region", "Within a country"],
  ];
  select.append(
    el("option", { value: "" }, `All countries (${nationals().length})`),
    el("option", { value: "custom", hidden: true }, "Chosen countries"),
    ...kinds.map(([kind, label]) => el("optgroup", { label }, ...(data.groups || []).filter((g) => g.kind === kind).map(option))),
  );
  select.value = state.group || (allCountries() ? "" : "custom");
  select.addEventListener("change", () => {
    const group = groupById(select.value);
    state.group = group ? group.id : "";
    state.countries = new Set(group ? group.countries : nationals());
    syncChips();
    render();
  });
}

// What the share button in the header shares: a category's page when only
// the type is chosen, else this page with its filters.
function viewLink() {
  const onlyCategory =
    state.category && !state.sort && !state.query && !state.shared && state.withdrawn && allCountries();
  return onlyCategory ? categoryLink(state.category) : location.href.split("#")[0];
}

// Build DOM without innerHTML, so names from the data are never parsed as HTML.
function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "style") node.style.cssText = value;
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  }
  node.append(...children.flat().filter((c) => c !== null && c !== undefined && c !== false && c !== ""));
  return node;
}

const englishName = (sign) => sign.names.en || sign.sign;
const localName = (sign, country) => sign.names[data.countries[country]?.language] || "";
const countryName = (code) => data.countries[code]?.name || code.toUpperCase();
const isWithdrawn = (sign) => Object.values(sign.countries).every((c) => c.valid_until);
const signAt = (category, slug) => signsByKey.get(`${category}/${slug}`);

// Countries, without regions of a country (US states, "us-ca"): what "All
// countries" shows. Regions are compared by choosing their group or ticking them.
const nationals = () => Object.keys(data.countries).filter((c) => !data.countries[c].region_of);
const regions = () => Object.keys(data.countries).filter((c) => data.countries[c].region_of);
const allCountries = () => state.countries.size === nationals().length && nationals().every((c) => state.countries.has(c));

// Countries with the sign itself. Variants of a sign (crosswind-from-left,
// speed-limit-50, …) have rows of their own and are not counted here, so a row
// only ever compares the very same sign.
const countriesOf = (sign) => Object.keys(sign.countries);

// Every filter but the type, which the type buttons count separately.
function matches(sign) {
  const present = countriesOf(sign).filter((c) => state.countries.has(c));
  if (!present.length) return false;
  if (state.shared && present.length < 2) return false;
  if (!state.withdrawn && isWithdrawn(sign)) return false;
  if (!state.query) return true;
  const haystack = [
    sign.sign,
    ...Object.values(sign.names),
    ...Object.values(sign.countries).map((c) => c.code),
  ]
    .join(" ")
    .toLowerCase();
  return state.query
    .toLowerCase()
    .split(/\s+/)
    .every((word) => haystack.includes(word));
}

// How many of the chosen countries have the sign.
const chosenCount = (sign) => countriesOf(sign).filter((c) => state.countries.has(c)).length;

// The signs in the order state.sort asks for; ties keep the default order.
function sorted(signs) {
  if (state.sort === "name") {
    return [...signs].sort((a, b) => englishName(a).localeCompare(englishName(b), "en", { sensitivity: "base" }));
  }
  if (state.sort.startsWith("countries")) {
    const sign = state.sort === "countries-asc" ? 1 : -1;
    const counts = new Map(signs.map((s) => [s, chosenCount(s)]));
    return [...signs].sort((a, b) => sign * (counts.get(a) - counts.get(b)));
  }
  return signs;
}

// An image shimmers as a placeholder until it has arrived (large drawings take
// a while), and says so if it cannot be loaded.
function image(src, alt, className) {
  if (!src) {
    return el("span", { class: ["missing", className].filter(Boolean).join(" "), title: "Image not downloaded yet" }, "no image yet");
  }
  const img = el("img", { src, alt, loading: "lazy", decoding: "async", class: [className, "pending"].filter(Boolean).join(" ") });
  img.addEventListener("load", () => img.classList.remove("pending"), { once: true });
  img.addEventListener(
    "error",
    () => img.replaceWith(el("span", { class: ["missing", className].filter(Boolean).join(" "), title: src }, "image failed to load")),
    { once: true },
  );
  return img;
}

function cell(sign, country) {
  const entry = sign.countries[country];
  const label = el("span", { class: "country" }, country.toUpperCase());
  if (!entry) {
    return el(
      "div",
      { class: "cell absent", title: `Not in ${countryName(country)}` },
      label,
      el("span", { class: "gap", "aria-label": `Not in ${countryName(country)}` }, "—"),
    );
  }
  const local = localName(sign, country);
  return el(
    "div",
    { class: "cell" },
    label,
    image(entry.image, `${countryName(country)}: ${local || englishName(sign)}`),
    el("code", {}, entry.code),
    local && el("span", { class: "local", title: local }, local),
    entry.valid_until && el("span", { class: "badge" }, `until ${entry.valid_until}`),
  );
}

const formatNumber = (n) => n.toLocaleString("en");

// Start over for new filters: the first PAGE_SIZE matching signs.
function render() {
  writeUrl();
  $("reset").hidden = isDefault();
  view.columns = Object.keys(data.countries).filter((c) => state.countries.has(c));
  const pool = data.signs.filter(matches);
  updateTypes(pool);
  const matching = sorted(state.category ? pool.filter((s) => s.category === state.category) : pool);
  // Display order: category by category, as listed in data.categories.
  view.signs = Object.keys(data.categories).flatMap((category) => matching.filter((s) => s.category === category));
  view.shown = 0;
  view.groups.clear();
  $("results").replaceChildren();
  if (!view.signs.length) {
    const again = el("button", { type: "button", class: "reset" }, "Reset filters");
    again.addEventListener("click", resetFilters);
    $("results").append(el("p", { class: "empty muted" }, "No signs match these filters. ", again));
  }
  showMore();
}

// Append the next PAGE_SIZE signs to their category tables.
function showMore() {
  const next = view.signs.slice(view.shown, view.shown + PAGE_SIZE);
  for (const sign of next) {
    groupFor(sign.category).append(row(sign));
  }
  view.shown += next.length;
  updateStatus();
  watchFooter();
}

// The table of one category, created when its first sign is shown.
function groupFor(category) {
  if (!view.groups.has(category)) {
    const total = view.signs.filter((s) => s.category === category).length;
    const head = el(
      "div",
      { class: "row head", role: "row" },
      el("span", { role: "columnheader" }, "Sign"),
      view.columns.map((c) => el("span", { role: "columnheader", class: "cell" }, countryName(c))),
    );
    const table = el("div", { class: "table", role: "table", style: `--columns: ${view.columns.length}` }, head);
    $("results").append(
      el(
        "section",
        { class: "group" },
        el(
          "h2",
          {},
          data.categories[category] || category,
          " ",
          el("small", {}, `(${formatNumber(total)})`),
          " ",
          shareButton(`Share ${data.categories[category] || category}`, categoryLink(category), data.categories[category] || category),
        ),
        table,
      ),
    );
    view.groups.set(category, table);
  }
  return view.groups.get(category);
}

function row(sign) {
  return el(
    "a",
    { class: "row", href: `#${sign.category}/${sign.sign}`, role: "row" },
    el("div", { class: "name" }, el("strong", {}, englishName(sign)), el("code", {}, sign.sign)),
    view.columns.map((c) => cell(sign, c)),
  );
}

// Short names for the type buttons; the full label is their tooltip.
const SHORT_TYPES = {
  warning: "Warning",
  regulatory: "Regulatory",
  information: "Information",
  "additional-panel": "Additional panels",
  "traffic-device": "Traffic devices",
  "traffic-signal": "Traffic signals",
};

// One button per type, each with how many signs the other filters leave in it.
function setupTypes() {
  const group = $("category");
  const button = (value, label, title) => {
    const node = el("button", { type: "button", class: "type", value, title }, el("span", {}, label), " ", el("small", { class: "count" }));
    node.addEventListener("click", () => {
      state.category = value;
      render();
    });
    return node;
  };
  group.append(
    button("", "All types", "Every type of sign"),
    ...Object.entries(data.categories).map(([value, label]) => button(value, SHORT_TYPES[value] || label, label)),
  );
}

function updateTypes(pool) {
  const counts = new Map();
  for (const sign of pool) counts.set(sign.category, (counts.get(sign.category) || 0) + 1);
  for (const node of $("category").querySelectorAll("button")) {
    const count = node.value ? counts.get(node.value) || 0 : pool.length;
    node.setAttribute("aria-pressed", String(node.value === state.category));
    node.querySelector(".count").textContent = formatNumber(count);
    node.classList.toggle("empty", !count);
  }
}

function updateStatus() {
  const total = data.signs.length;
  const matching = view.signs.length;
  const scope = matching === total ? `${formatNumber(total)} signs` : `${formatNumber(matching)} matching (${formatNumber(total)} in all)`;
  // The chosen countries, and regions (US states) by their label.
  const countries = view.columns.filter((c) => !data.countries[c].region_of).length;
  const places = [`${countries} ${countries === 1 ? "country" : "countries"}`];
  const byLabel = new Map();
  for (const c of view.columns.filter((c) => data.countries[c].region_of)) {
    const label = data.countries[c].region_label || `${data.countries[c].region_of.toUpperCase()} regions`;
    byLabel.set(label, (byLabel.get(label) || 0) + 1);
  }
  for (const [label, count] of byLabel) places.push(`${count} ${label}`);
  $("summary").textContent = `${formatNumber(view.shown)} of ${scope} · ${places.join(", ")}`;
  const remaining = matching - view.shown;
  const more = $("more");
  more.hidden = remaining <= 0;
  $("more-button").textContent = `Show ${formatNumber(Math.min(PAGE_SIZE, remaining))} more`;
  $("more-status").textContent = `Showing ${formatNumber(view.shown)} of ${formatNumber(matching)} signs`;
}

function detail(sign) {
  const panels = Object.entries(sign.countries).map(([country, entry]) => {
    const local = localName(sign, country);
    return el(
      "section",
      { class: "panel" },
      el("h3", {}, countryName(country), " ", entry.valid_until && el("span", { class: "badge" }, `valid until ${entry.valid_until}`)),
      image(entry.image, `${countryName(country)}: ${local || englishName(sign)}`, "big"),
      el(
        "dl",
        {},
        el("dt", {}, "Code"),
        el("dd", {}, entry.code),
        local && [el("dt", {}, "Name"), el("dd", {}, local)],
        entry.author && [el("dt", {}, "Author"), el("dd", {}, entry.author)],
        entry.license && [el("dt", {}, "Licence"), el("dd", {}, entry.license)],
        entry.source && [el("dt", {}, "Source"), el("dd", {}, el("a", { href: entry.source, target: "_blank", rel: "noopener" }, "Wikimedia Commons"))],
      ),
      Boolean(entry.archived?.length) &&
        el(
          "div",
          { class: "archive" },
          entry.archived.map((old) =>
            el("figure", {}, image(old.image, `Earlier image, valid until ${old.valid_until}`), el("figcaption", { class: "muted" }, `until ${old.valid_until}`)),
          ),
        ),
    );
  });
  const parent = sign.variant_of && signAt(sign.category, sign.variant_of);
  const link = (s) => el("a", { href: `#${s.category}/${s.sign}` }, englishName(s));
  const variants = (sign.variants || []).map((slug) => signAt(sign.category, slug)).filter(Boolean);
  return [
    el("div", { class: "detail-head" }, el("h2", { id: "detail-title" }, englishName(sign)), shareButton(`Share ${englishName(sign)}`, signLink(sign), englishName(sign))),
    el("p", { class: "muted" }, `${data.categories[sign.category] || sign.category} · `, el("code", {}, sign.sign)),
    parent && el("p", { class: "muted" }, "Variant of ", link(parent)),
    variants.length > 0 && el("p", { class: "muted variants" }, "Variants: ", variants.flatMap((v, i) => (i ? [", ", link(v)] : [link(v)]))),
    el(
      "ul",
      { class: "names" },
      Object.entries(sign.names).map(([lang, name]) => el("li", {}, el("span", { class: "muted" }, `${lang}: `), name)),
    ),
    el("div", { class: "compare" }, panels),
  ].filter(Boolean);
}

function route() {
  const dialog = $("detail");
  const key = decodeURIComponent(location.hash.slice(1));
  const sign = data.signs.find((s) => `${s.category}/${s.sign}` === key);
  if (!sign) {
    if (dialog.open) dialog.close();
    return;
  }
  $("detail-body").replaceChildren(...detail(sign));
  if (!dialog.open) dialog.showModal();
}

function setupControls() {
  // Filters start open where there is room for them, folded on phones.
  $("filters").open = window.matchMedia("(min-width: 641px)").matches;

  setupTypes();
  const sort = $("sort");
  sort.append(...Object.entries(SORTS).map(([value, label]) => el("option", { value }, label)));
  sort.value = state.sort;
  sort.addEventListener("change", () => {
    state.sort = sort.value;
    render();
  });
  $("search").value = state.query;
  $("shared").checked = state.shared;
  $("withdrawn").checked = state.withdrawn;
  $("share-view").addEventListener("click", () => share(viewLink(), document.title));
  $("reset").addEventListener("click", resetFilters);

  const chips = $("countries");
  const chip = (code) => {
    const box = el("input", { type: "checkbox", checked: state.countries.has(code), value: code });
    box.addEventListener("change", () => chooseCountries((chosen) => (box.checked ? chosen.add(code) : chosen.delete(code))));
    return el("label", { title: countryName(code) }, box, code.toUpperCase());
  };
  // "All" and "None" for a set of chips: they add or remove only those countries.
  const bulk = (codes, all, none) => {
    const button = (label, title, update) => {
      const node = el("button", { type: "button", class: "bulk", title }, label);
      node.addEventListener("click", () => chooseCountries((chosen) => codes.forEach((c) => update(chosen, c))));
      return node;
    };
    return el(
      "span",
      { class: "bulk-buttons" },
      button("All", all, (chosen, c) => chosen.add(c)),
      button("None", none, (chosen, c) => chosen.delete(c)),
    );
  };
  chips.append(bulk(nationals(), "Select every country", "Clear the countries"), ...nationals().map(chip));
  // Regions (US states, …) fold away behind one chip per country, so the row stays short.
  const byCountry = new Map();
  for (const code of regions()) {
    const country = data.countries[code].region_of;
    byCountry.set(country, [...(byCountry.get(country) || []), code]);
  }
  for (const [country, codes] of byCountry) {
    const label = data.countries[codes[0]].region_label || `${country.toUpperCase()} regions`;
    const open = codes.some((c) => state.countries.has(c));
    // "Select all" adds every region next to the countries already chosen;
    // the Countries menu's group compares the regions on their own.
    const all = el("button", { type: "button", class: "bulk" }, `Select all ${label}`);
    all.addEventListener("click", () => chooseCountries((chosen) => codes.forEach((c) => chosen.add(c))));
    const none = el("button", { type: "button", class: "bulk" }, "Clear");
    none.addEventListener("click", () => chooseCountries((chosen) => codes.forEach((c) => chosen.delete(c))));
    chips.append(
      el(
        "details",
        { class: "regions", open },
        el("summary", {}, `${label} (${codes.length})`),
        el("div", { class: "chips" }, el("span", { class: "bulk-buttons" }, all, none), ...codes.map(chip)),
      ),
    );
  }
  // Comparing needs at least two countries.
  $("shared").disabled = Object.keys(data.countries).length < 2;

  let timer;
  $("search").addEventListener("input", (event) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.query = event.target.value.trim();
      render();
    }, 120);
  });
  for (const id of ["shared", "withdrawn"]) {
    $(id).addEventListener("change", (event) => {
      state[id] = event.target.checked;
      render();
    });
  }

  $("detail").addEventListener("close", () => {
    if (location.hash) history.pushState("", document.title, location.pathname + location.search);
  });
  window.addEventListener("hashchange", route);
}

// Load more signs before the reader reaches the end of the list.
let observer;

function setupInfiniteScroll() {
  $("more-button").addEventListener("click", showMore);
  if (!("IntersectionObserver" in window)) return; // the button still works
  observer = new IntersectionObserver(
    (seen) => {
      if (seen.some((entry) => entry.isIntersecting) && view.shown < view.signs.length) showMore();
    },
    { rootMargin: "0px 0px 800px 0px" },
  );
  observer.observe($("more"));
}

// Observing again reports the footer's current visibility, so a screen that
// still has room after a batch (or after new filters) gets the next one.
function watchFooter() {
  if (!observer) return;
  observer.unobserve($("more"));
  observer.observe($("more"));
}

// Download data.json and report progress as it arrives.
async function load() {
  const response = await fetch("data.json");
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  // Content-Length is the compressed size when the server gzips, so a
  // percentage is only shown for an uncompressed response.
  const length = response.headers.get("Content-Encoding") ? 0 : Number(response.headers.get("Content-Length")) || 0;
  if (!response.body || !response.body.getReader) return response.json();
  const reader = response.body.getReader();
  const chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    loading(received, length);
  }
  const bytes = new Uint8Array(received);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  $("loading-text").textContent = "Preparing the signs…";
  return JSON.parse(new TextDecoder().decode(bytes));
}

function loading(received, length) {
  const kb = (n) => `${formatNumber(Math.round(n / 1024))} KB`;
  const bar = $("loading-bar");
  if (length) {
    bar.max = length;
    bar.value = Math.min(received, length);
    $("loading-text").textContent = `Loading signs… ${kb(received)} of ${kb(length)}`;
  } else {
    bar.removeAttribute("value"); // indeterminate
    $("loading-text").textContent = `Loading signs… ${kb(received)}`;
  }
  $("summary").textContent = `Loading… ${kb(received)}`;
}

async function start() {
  try {
    data = await load();
  } catch (error) {
    $("loading-text").textContent = `Could not load data.json (${error.message}).`;
    $("loading-bar").hidden = true;
    $("summary").textContent = "Could not load the signs.";
    return;
  }
  for (const sign of data.signs) signsByKey.set(`${sign.category}/${sign.sign}`, sign);
  $("loading").hidden = true;
  $("loading").removeAttribute("aria-busy");
  readUrl();
  setupControls();
  setupGroups();
  setupInfiniteScroll();
  render();
  route();
}

start();
