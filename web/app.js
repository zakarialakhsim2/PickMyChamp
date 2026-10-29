const $ = (selector) => document.querySelector(selector);
let lookupSequence = 0;
let playbookSequence = 0;
let playbookWasGenerated = false;
let syncedEnemyLanePick = null;
const championIds = new Map();
let championCatalog = [];
let activeChampionOption = -1;
const PROFILE_STORAGE_KEY = "pickmychamp.profile";

function splitList(value) {
  return value.split(",").map((part) => part.trim()).filter(Boolean);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function setFeedback(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("feedback-error", isError);
}

function updateEnemyStage() {
  const select = $("#enemy-champion");
  const option = select.options[select.selectedIndex];
  const championName = option && option.value ? option.value : "Vayne";
  const championId = option && option.dataset.championId ? option.dataset.championId : "Vayne";
  const image = $("#enemy-art");
  const fallback = $("#enemy-art-fallback");
  $("#enemy-stage-name").textContent = championName;
  image.alt = `${championName} splash art`;
  image.hidden = false;
  fallback.hidden = true;
  image.onerror = () => {
    image.hidden = true;
    fallback.textContent = championName.slice(0, 1).toUpperCase();
    fallback.hidden = false;
  };
  image.src = championSplashUrl(championId);
}

function championAssetUrl(assetType, championId) {
  return `/api/champion-asset/${assetType}/${encodeURIComponent(championId)}`;
}

function championPortraitUrl(championId) {
  return championAssetUrl("portrait", championId);
}

function championSplashUrl(championId) {
  return championAssetUrl("splash", championId);
}

function renderChampionOptions(query = "") {
  const list = $("#champion-picker-options");
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const matches = championCatalog.filter((champion) =>
    champion.name.toLocaleLowerCase().includes(normalizedQuery)
  );
  list.replaceChildren();
  activeChampionOption = -1;

  if (!matches.length) {
    const empty = document.createElement("div");
    empty.className = "champion-picker-empty";
    empty.textContent = "No champions found";
    empty.setAttribute("role", "option");
    empty.setAttribute("aria-disabled", "true");
    list.append(empty);
    return;
  }

  const selectedName = $("#enemy-champion").value;
  matches.forEach((champion, index) => {
    const option = document.createElement("button");
    option.className = "champion-picker-option";
    option.type = "button";
    option.id = `champion-option-${index}`;
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", String(champion.name === selectedName));
    option.dataset.championName = champion.name;

    const art = document.createElement("span");
    art.className = "champion-option-art";
    const initial = document.createElement("span");
    initial.textContent = champion.name.slice(0, 1).toUpperCase();
    initial.setAttribute("aria-hidden", "true");
    const image = document.createElement("img");
    image.src = championPortraitUrl(champion.id);
    image.alt = "";
    image.loading = "lazy";
    image.decoding = "async";
    image.addEventListener("error", () => { image.hidden = true; }, { once: true });
    art.append(initial, image);

    const name = document.createElement("span");
    name.className = "champion-option-name";
    name.textContent = champion.name;
    option.append(art, name);
    option.addEventListener("click", () => selectChampion(champion));
    list.append(option);
  });
}

function updateChampionPicker(champion) {
  if (!champion) return;
  const input = $("#champion-search");
  const picker = $("#champion-picker");
  const image = $("#champion-picker-image");
  input.value = champion.name;
  $("#champion-picker-initial").textContent = champion.name.slice(0, 1).toUpperCase();
  picker.classList.add("has-selection");
  image.hidden = false;
  image.onerror = () => { image.hidden = true; };
  image.src = championPortraitUrl(champion.id);
}

function setActiveChampionOption(index) {
  const options = [...$("#champion-picker-options").querySelectorAll("[role='option']:not([aria-disabled='true'])")];
  if (!options.length) return;
  activeChampionOption = (index + options.length) % options.length;
  options.forEach((option, optionIndex) => option.classList.toggle("active", optionIndex === activeChampionOption));
  const activeOption = options[activeChampionOption];
  $("#champion-search").setAttribute("aria-activedescendant", activeOption.id);
  activeOption.scrollIntoView({ block: "nearest" });
}

function openChampionPicker(query = "") {
  const input = $("#champion-search");
  const toggle = $("#champion-picker-toggle");
  $("#champion-picker-options").hidden = false;
  input.setAttribute("aria-expanded", "true");
  toggle.setAttribute("aria-expanded", "true");
  renderChampionOptions(query);
}

function closeChampionPicker() {
  $("#champion-picker-options").hidden = true;
  $("#champion-search").setAttribute("aria-expanded", "false");
  $("#champion-search").removeAttribute("aria-activedescendant");
  $("#champion-picker-toggle").setAttribute("aria-expanded", "false");
}

function selectChampion(champion) {
  const select = $("#enemy-champion");
  select.value = champion.name;
  updateChampionPicker(champion);
  closeChampionPicker();
  updateEnemyStage();
  syncEnemyLanePick();
  loadCounter(new Event("submit"));
  if (playbookWasGenerated) loadPlaybook();
}

function populateDraftSlots() {
  document.querySelectorAll(".draft-slot").forEach((select) => {
    const selected = select.value;
    const options = [
      new Option("Not revealed", ""),
      ...championCatalog.map((champion) => new Option(champion.name, champion.name)),
    ];
    select.replaceChildren(...options);
    if (championCatalog.some((champion) => champion.name === selected)) {
      select.value = selected;
    }
  });
}

function syncEnemyLanePick() {
  const role = $("#draft-role").value;
  const enemyChampion = $("#enemy-champion").value;
  if (syncedEnemyLanePick && syncedEnemyLanePick.role !== role) {
    const previousLanePick = document.querySelector(
      `.draft-slot[data-team="enemies"][data-role="${syncedEnemyLanePick.role}"]`
    );
    if (previousLanePick && previousLanePick.value === syncedEnemyLanePick.champion) {
      previousLanePick.value = "";
    }
  }
  const lanePick = document.querySelector(
    `.draft-slot[data-team="enemies"][data-role="${role}"]`
  );
  if (lanePick) lanePick.value = enemyChampion;
  syncedEnemyLanePick = enemyChampion
    ? { role, champion: enemyChampion }
    : null;
}

function collectDraftTeam(team) {
  const picks = {};
  document.querySelectorAll(`.draft-slot[data-team="${team}"]`).forEach((select) => {
    if (select.value) picks[select.dataset.role] = select.value;
  });
  return picks;
}

function appendRoleJob(list, item) {
  const row = document.createElement("li");
  const title = document.createElement("strong");
  const job = document.createElement("span");
  title.textContent = `${item.label} · ${item.champion}`;
  job.textContent = item.job;
  row.append(title, job);
  list.append(row);
}

function setPlaybookDetail(id, value) {
  const element = $(`#${id}`);
  element.textContent = value || "";
  element.closest(".playbook-detail").hidden = !value;
}

function renderPlaybook(playbook) {
  const allied = playbook.allied_coverage;
  const enemy = playbook.enemy_coverage;
  $("#playbook-allied-pattern").textContent = playbook.allied_pattern.label;
  $("#playbook-win-condition").textContent = playbook.allied_pattern.win_condition;
  $("#playbook-your-job").textContent = playbook.your_champion
    ? `${playbook.your_champion} (${playbook.your_role}): ${playbook.your_job}`
    : `${playbook.your_role}: ${playbook.your_job}`;
  setPlaybookDetail("playbook-avoid", playbook.allied_pattern.avoid);
  setPlaybookDetail("playbook-fallback", playbook.allied_pattern.fallback);
  const evidence = playbook.evidence.map(
    (item) => `${item.role.toUpperCase()}: ${item.champion}`
  ).join(" · ");
  setPlaybookDetail(
    "playbook-evidence",
    evidence || "No single supported signal stands out for this draft."
  );
  $("#playbook-enemy-pattern").textContent = playbook.enemy_pattern.label;
  $("#playbook-enemy-read").textContent = playbook.enemy_read;
  $("#playbook-counter-plan").textContent = playbook.counter_plan;
  $("#playbook-coverage").textContent =
    `ALLIES ${allied.selected}/5 · ${allied.profiled} PROFILED | ` +
    `OPPONENTS ${enemy.selected}/5 · ${enemy.profiled} PROFILED`;
  $("#playbook-team-coverage").textContent =
    `Your team: ${allied.selected} of 5 roles filled; ${allied.profiled} of those picks have a curated profile. ` +
    `Opponents: ${enemy.selected} of 5 roles filled; ${enemy.profiled} profiled.`;

  const roleJobs = $("#playbook-role-jobs");
  roleJobs.replaceChildren();
  playbook.role_jobs.forEach((item) => appendRoleJob(roleJobs, item));
  if (!playbook.role_jobs.length) {
    const empty = document.createElement("li");
    empty.textContent = "Role assignments will appear when a supported team pattern is detected.";
    roleJobs.append(empty);
  }
  $("#playbook-notes").textContent = playbook.notes.join(" ");
  $("#playbook-results").hidden = false;
}

async function loadPlaybook(event) {
  if (event) event.preventDefault();
  const sequence = ++playbookSequence;
  const error = $("#playbook-error");
  const results = $("#playbook-results");
  const button = $("#playbook-form button[type='submit']");
  const allies = collectDraftTeam("allies");
  const enemies = collectDraftTeam("enemies");
  error.hidden = true;
  results.hidden = true;
  if (!Object.keys(allies).length || !Object.keys(enemies).length) {
    error.textContent = "Add at least one champion to each team.";
    error.hidden = false;
    return;
  }

  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    const playbook = await requestJson("/api/playbook", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        allies,
        enemies,
        player_role: $("#draft-role").value,
      }),
    });
    if (sequence !== playbookSequence) return;
    renderPlaybook(playbook);
    playbookWasGenerated = true;
  } catch (requestError) {
    if (sequence !== playbookSequence) return;
    error.textContent = requestError.message;
    error.hidden = false;
  } finally {
    if (sequence === playbookSequence) {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }
}

function setupChampionPicker() {
  const input = $("#champion-search");
  const toggle = $("#champion-picker-toggle");
  input.addEventListener("focus", () => {
    const query = input.value === $("#enemy-champion").value ? "" : input.value;
    openChampionPicker(query);
    if (!query) input.select();
  });
  input.addEventListener("input", () => openChampionPicker(input.value));
  input.addEventListener("keydown", (event) => {
    const options = $("#champion-picker-options").querySelectorAll("[role='option']:not([aria-disabled='true'])");
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if ($("#champion-picker-options").hidden) openChampionPicker(input.value === $("#enemy-champion").value ? "" : input.value);
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const nextIndex = activeChampionOption < 0 && direction < 0
        ? options.length - 1
        : activeChampionOption + direction;
      setActiveChampionOption(nextIndex);
    } else if (event.key === "Enter" && !$("#champion-picker-options").hidden) {
      event.preventDefault();
      const active = options[activeChampionOption] || options[0];
      if (active && active.dataset.championName) {
        const champion = championCatalog.find((entry) => entry.name === active.dataset.championName);
        if (champion) selectChampion(champion);
      }
    } else if (event.key === "Escape") {
      closeChampionPicker();
    }
  });
  toggle.addEventListener("click", () => {
    if ($("#champion-picker-options").hidden) {
      input.focus();
      openChampionPicker("");
    } else {
      closeChampionPicker();
    }
  });
  document.addEventListener("click", (event) => {
    if (!$("#champion-picker").contains(event.target)) closeChampionPicker();
  });
}

function updateProfileRoleBadge() {
  const select = $("#primary-role");
  const badge = $("#profile-role-badge");
  const option = select.options[select.selectedIndex];
  badge.textContent = option && select.value ? option.textContent.split(" / ")[0] : "—";
}

function setupAds() {
  const client = window.PICKMYCHAMP_ADSENSE_CLIENT || "";
  const container = $("#ad-container");
  if (!client || !/^ca-pub-\d+$/.test(client)) return;
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(client)}`;
  script.crossOrigin = "anonymous";
  document.head.append(script);
  container.replaceChildren();
  const ad = document.createElement("ins");
  ad.className = "adsbygoogle";
  ad.style.display = "block";
  ad.dataset.adClient = client;
  ad.dataset.adFormat = "auto";
  ad.dataset.fullWidthResponsive = "true";
  container.append(ad);
  script.addEventListener("load", () => {
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (error) {
      container.replaceChildren(document.createTextNode("Advertisement unavailable."));
    }
  });
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP error ${response.status}`);
  return payload;
}

function renderCard(pick, index) {
  const card = document.createElement("article");
  card.className = "pick-card";
  const champion = escapeHtml(pick.champion);
  const initial = escapeHtml(pick.champion.slice(0, 1));
  const championId = championIds.get(pick.champion.toLocaleLowerCase())
    || pick.champion.replace(/[^A-Za-z0-9]/g, "");
  const build = pick.build.map(escapeHtml).join(" → ");
  const buildMarkup = pick.guide_available
    ? `<strong>${escapeHtml(pick.starting_item)}</strong><strong>${build}</strong>`
    : `<strong>Build data is not in the counter table.</strong><a class="source-link" href="${escapeHtml(pick.build_url)}" target="_blank" rel="noopener noreferrer">Open English build guide ↗</a>`;
  const situations = pick.situational_items
    .map(({ item, reason }) => `<li><b>${escapeHtml(item)}</b> — ${escapeHtml(reason)}</li>`)
    .join("");

  card.innerHTML = `
    <div class="pick-art">
      <span class="pick-art-mark" aria-hidden="true">${initial}</span>
      <img src="${escapeHtml(championSplashUrl(championId))}" alt="" loading="lazy" decoding="async">
      <span class="pick-number">0${index + 1}</span>
      <span class="pick-badge">${pick.has_stats ? `${pick.win_rate.toFixed(2)}% · ${pick.games.toLocaleString("en-US")} GAMES` : "CURATED GUIDE"}</span>
    </div>
    <div class="pick-top">
      <span class="champion-icon" aria-hidden="true">${initial}</span>
      <div class="pick-title"><h3>${champion}</h3><p>${escapeHtml(pick.reason)}</p></div>
    </div>
    <div class="pick-details">
      <div class="detail-cell"><span>SUPPORT TO REQUEST</span><strong class="gold-text">${escapeHtml(pick.support)}</strong><strong>Alternative: ${escapeHtml(pick.support_alternative)}</strong></div>
      <div class="detail-cell"><span>RUNES</span><strong>${escapeHtml(pick.runes)}</strong><strong>${escapeHtml(pick.rune_shards)}</strong></div>
      <div class="detail-cell"><span>SUMMONER SPELLS & SKILLS</span><strong>${escapeHtml(pick.spells)}</strong><strong>${escapeHtml(pick.skills)}</strong></div>
      <div class="detail-cell"><span>START & BUILD</span>${buildMarkup}</div>
    </div>
    <button class="expand-button" type="button" aria-expanded="false"><span>${pick.guide_available ? "See lane plan and situational items" : "See data limits and matchup source"}</span><b>＋</b></button>
    <div class="extra-details" hidden>
      <div><h4>${pick.guide_available ? "LANE PLAN" : "MATCHUP DATA"}</h4><p>${escapeHtml(pick.lane_plan)}</p></div>
      <div><h4>${pick.guide_available ? "SITUATIONAL ITEMS" : "SUPPORT & BUILD"}</h4><p>${escapeHtml(pick.support)}. ${escapeHtml(pick.support_alternative)}.</p><ul>${situations}</ul></div>
    </div>`;
  const expand = card.querySelector(".expand-button");
  const details = card.querySelector(".extra-details");
  const portrait = card.querySelector(".pick-art img");
  portrait.addEventListener("error", () => {
    portrait.hidden = true;
    card.classList.add("portrait-missing");
  }, { once: true });
  expand.addEventListener("click", () => {
    const expanded = expand.getAttribute("aria-expanded") === "true";
    expand.setAttribute("aria-expanded", String(!expanded));
    details.hidden = expanded;
    expand.querySelector("b").textContent = expanded ? "＋" : "−";
  });
  return card;
}

async function loadCounter(event) {
  event.preventDefault();
  const sequence = ++lookupSequence;
  const enemySelect = $("#enemy-champion");
  const selectedEnemy = enemySelect.value.trim();
  const searchValue = $("#champion-search").value.trim();
  const enemy = selectedEnemy.toLocaleLowerCase() === searchValue.toLocaleLowerCase()
    ? selectedEnemy
    : "";
  const role = $("#draft-role").value;
  const error = $("#error-message");
  const loading = $("#loading-message");
  const results = $("#results-section");
  error.hidden = true;
  results.hidden = true;
  if (!enemy) {
    error.textContent = "Select the enemy champion.";
    error.hidden = false;
    return;
  }
  loading.hidden = false;
  try {
    const data = await requestJson(
      `/api/counter?enemy=${encodeURIComponent(enemy)}&role=${encodeURIComponent(role)}`
    );
    if (sequence !== lookupSequence) return;
    $("#enemy-label").textContent = data.enemy;
    $("#result-patch").textContent = data.patch;
    $("#result-patch").textContent = `${data.source} · ${data.scope} · ${data.enemy_role || role} · Patch ${data.patch}`;
    const list = $("#recommendation-list");
    list.replaceChildren(...data.picks.map(renderCard));
    if (!data.picks.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = data.fallback_message || "No matchup data is available right now.";
      list.append(empty);
    }
    const disclaimer = document.querySelector(".disclaimer p");
    disclaimer.innerHTML = `${data.role_warning ? `<b>Lane note</b> — ${escapeHtml(data.role_warning)} ` : ""}${data.fallback_message ? `<b>Note</b> — ${escapeHtml(data.fallback_message)} ` : ""}<b>Matchup source</b> — ${escapeHtml(data.source)} ${escapeHtml(data.scope)} patch ${escapeHtml(data.patch)}. <a class="source-link" href="${escapeHtml(data.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`;
    results.hidden = false;
  } catch (requestError) {
    if (sequence !== lookupSequence) return;
    error.textContent = requestError.message;
    error.hidden = false;
  } finally {
    if (sequence === lookupSequence) loading.hidden = true;
  }
}

function showPage(name) {
  const isDraft = name === "draft";
  $("#draft-page").hidden = !isDraft;
  $("#profile-page").hidden = isDraft;
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === name);
  });
  $("#breadcrumb-current").textContent = isDraft ? "DRAFT ASSISTANT" : "MY PROFILE";
}

async function loadProfile() {
  let profile;
  const storedProfile = localStorage.getItem(PROFILE_STORAGE_KEY);
  if (storedProfile) {
    try {
      profile = JSON.parse(storedProfile);
      if (!profile.role_confirmed) {
        profile.primary_role = "";
      }
    } catch (error) {
      localStorage.removeItem(PROFILE_STORAGE_KEY);
      console.warn("Stored profile was invalid and has been cleared.", error);
    }
  }
  if (!profile) profile = await requestJson("/api/profile");
  if (!profile.role_confirmed) profile.primary_role = "";
  $("#profile-status").textContent = profile.configured
    ? `${profile.riot_id} · ${profile.region.toUpperCase()}`
    : "Profile not configured";
  if (!profile.configured) return;
  $("#riot-id").value = profile.riot_id;
  $("#profile-region").value = profile.region;
  $("#primary-role").value = profile.primary_role || "";
  updateProfileRoleBadge();
  $("#secondary-roles").value = profile.secondary_roles.join(", ");
  $("#mastered-champions").value = profile.mastered_champions.join(", ");
  $("#play-preferences").value = profile.preferences.join(", ");
}

async function loadChampions() {
  const select = $("#enemy-champion");
  try {
    const data = await requestJson("/api/champions");
    championCatalog = data.champions;
    championIds.clear();
    const options = data.champions.map((champion) => {
      championIds.set(champion.name.toLocaleLowerCase(), champion.id);
      const option = document.createElement("option");
      option.value = champion.name;
      option.textContent = champion.name;
      option.dataset.championId = champion.id;
      return option;
    });
    select.replaceChildren(...options);
    const vayne = data.champions.find(
      (champion) => champion.name.toLocaleLowerCase() === "vayne"
    );
    if (vayne) select.value = vayne.name;
    populateDraftSlots();
    select.disabled = false;
    $("#champion-search").disabled = false;
    $("#champion-picker-toggle").disabled = false;
    $("#patch-label").textContent = data.patch;
    updateChampionPicker(vayne || data.champions[0]);
    updateEnemyStage();
    syncEnemyLanePick();
    await loadCounter(new Event("submit"));
  } catch (error) {
    $("#error-message").textContent = error.message;
    $("#error-message").hidden = false;
    select.replaceChildren(new Option("Champion list unavailable", ""));
    $("#champion-search").disabled = true;
    $("#champion-picker-toggle").disabled = true;
    updateEnemyStage();
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const feedback = $("#profile-feedback");
  setFeedback(feedback, "Saving…");
  const payload = {
    riot_id: $("#riot-id").value.trim(),
    region: $("#profile-region").value,
    primary_role: $("#primary-role").value,
    secondary_roles: splitList($("#secondary-roles").value),
    mastered_champions: splitList($("#mastered-champions").value),
    preferences: splitList($("#play-preferences").value),
  };
  try {
    const riotIdParts = payload.riot_id.split("#");
    if (riotIdParts.length !== 2 || !riotIdParts[0].trim() || !riotIdParts[1].trim()) {
      throw new Error("Riot ID must use the Name#TAG format.");
    }
    if (!payload.primary_role) {
      throw new Error("Select your primary role before saving.");
    }
    const profile = {
      configured: true,
      ...payload,
      primary_role: payload.primary_role.toLowerCase(),
      role_confirmed: true,
    };
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
    $("#profile-status").textContent = `${profile.riot_id} · ${profile.region.toUpperCase()}`;
    setFeedback(feedback, "Profile saved in this browser.");
  } catch (requestError) {
    setFeedback(feedback, requestError.message, true);
  }
}

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => showPage(button.dataset.page));
});
$("#counter-form").addEventListener("submit", loadCounter);
$("#enemy-champion").addEventListener("change", () => {
  const champion = championCatalog.find((entry) => entry.name === $("#enemy-champion").value);
  if (champion) updateChampionPicker(champion);
  updateEnemyStage();
  syncEnemyLanePick();
  loadCounter(new Event("submit"));
  if (playbookWasGenerated) loadPlaybook();
});
$("#draft-role").addEventListener("change", () => {
  syncEnemyLanePick();
  loadCounter(new Event("submit"));
  if (playbookWasGenerated) loadPlaybook();
});
$("#profile-form").addEventListener("submit", saveProfile);
$("#playbook-form").addEventListener("submit", loadPlaybook);
document.querySelectorAll(".draft-slot").forEach((select) => {
  select.addEventListener("change", () => {
    if (playbookWasGenerated) loadPlaybook();
  });
});
$("#primary-role").addEventListener("change", updateProfileRoleBadge);
updateProfileRoleBadge();
setupChampionPicker();
setupAds();
loadChampions();
loadProfile().catch((error) => {
  $("#profile-status").textContent = "Profile unavailable";
  setFeedback($("#profile-feedback"), error.message, true);
});
