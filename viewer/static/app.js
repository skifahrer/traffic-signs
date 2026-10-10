// Traffic signs viewer: one row per sign, one column per country.
// Data comes from data.json (built by `python3 -m viewer`).

const state = { query: "", category: "", countries: new Set(), shared: false, withdrawn: true };
let data;

const $ = (id) => document.getElementById(id);

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

function matches(sign) {
  if (state.category && sign.category !== state.category) return false;
  const present = Object.keys(sign.countries).filter((c) => state.countries.has(c));
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

function image(src, alt, className) {
  return src
    ? el("img", { src, alt, loading: "lazy", decoding: "async", class: className })
    : el("span", { class: ["missing", className].filter(Boolean).join(" "), title: "Image not downloaded yet" }, "no image yet");
}

function cell(sign, country) {
  const entry = sign.countries[country];
  const label = el("span", { class: "country" }, country.toUpperCase());
  if (!entry) {
    return el("div", { class: "cell absent", title: `Not in ${countryName(country)}` }, label, el("span", { "aria-label": `Not in ${countryName(country)}` }, "—"));
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

function render() {
  const columns = Object.keys(data.countries).filter((c) => state.countries.has(c));
  const shown = data.signs.filter(matches);
  const results = $("results");
  results.replaceChildren();
  $("summary").textContent =
    `${shown.length} of ${data.signs.length} signs · ${Object.keys(data.countries).length} ` +
    `${Object.keys(data.countries).length === 1 ? "country" : "countries"}`;

  if (!shown.length) {
    results.append(el("p", { class: "empty muted" }, "No signs match these filters."));
    return;
  }

  for (const [category, label] of Object.entries(data.categories)) {
    const signs = shown.filter((s) => s.category === category);
    if (!signs.length) continue;
    const head = el(
      "div",
      { class: "row head", role: "row" },
      el("span", { role: "columnheader" }, "Sign"),
      columns.map((c) => el("span", { role: "columnheader", class: "cell" }, countryName(c))),
    );
    const rows = signs.map((sign) =>
      el(
        "a",
        { class: "row", href: `#${sign.category}/${sign.sign}`, role: "row" },
        el("div", { class: "name" }, el("strong", {}, englishName(sign)), el("code", {}, sign.sign)),
        columns.map((c) => cell(sign, c)),
      ),
    );
    results.append(
      el(
        "section",
        { class: "group" },
        el("h2", {}, label, " ", el("small", {}, `(${signs.length})`)),
        el("div", { class: "table", role: "table", style: `--columns: ${columns.length}` }, head, rows),
      ),
    );
  }
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
  return [
    el("h2", { id: "detail-title" }, englishName(sign)),
    el("p", { class: "muted" }, `${data.categories[sign.category] || sign.category} · `, el("code", {}, sign.sign)),
    el(
      "ul",
      { class: "names" },
      Object.entries(sign.names).map(([lang, name]) => el("li", {}, el("span", { class: "muted" }, `${lang}: `), name)),
    ),
    el("div", { class: "compare" }, panels),
  ];
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

  const category = $("category");
  category.append(
    el("option", { value: "" }, "All types"),
    Object.entries(data.categories).map(([value, label]) => el("option", { value }, label)),
  );
  category.addEventListener("change", () => {
    state.category = category.value;
    render();
  });

  const chips = $("countries");
  for (const code of Object.keys(data.countries)) {
    state.countries.add(code);
    const box = el("input", { type: "checkbox", checked: true, value: code });
    box.addEventListener("change", () => {
      box.checked ? state.countries.add(code) : state.countries.delete(code);
      render();
    });
    chips.append(el("label", { title: countryName(code) }, box, code.toUpperCase()));
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

async function start() {
  try {
    const response = await fetch("data.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();
  } catch (error) {
    $("summary").textContent = `Could not load data.json (${error.message}).`;
    return;
  }
  setupControls();
  render();
  route();
}

start();
