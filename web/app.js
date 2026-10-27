const $ = (selector) => document.querySelector(selector);
let lookupSequence = 0;

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
  const build = pick.build.map(escapeHtml).join(" → ");
  const buildMarkup = pick.guide_available
    ? `<strong>${escapeHtml(pick.starting_item)}</strong><strong>${build}</strong>`
    : `<strong>Build data is not in the counter table.</strong><a class="source-link" href="${escapeHtml(pick.build_url)}" target="_blank" rel="noopener noreferrer">Open English build guide ↗</a>`;
  const situations = pick.situational_items
    .map(({ item, reason }) => `<li><b>${escapeHtml(item)}</b> — ${escapeHtml(reason)}</li>`)
    .join("");

  card.innerHTML = `
    <div class="pick-top">
      <span class="pick-number">0${index + 1}</span>
      <span class="champion-icon" aria-hidden="true">${initial}</span>
      <div class="pick-title"><h3>${champion}</h3><p>${escapeHtml(pick.reason)}</p></div>
      <span class="pick-badge">${pick.has_stats ? `${pick.win_rate.toFixed(2)}% · ${pick.games.toLocaleString("en-US")} games` : "CURATED GUIDE"}</span>
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
  const enemy = enemySelect.value.trim();
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
  const profile = await requestJson("/api/profile");
  $("#profile-status").textContent = profile.configured
    ? `${profile.riot_id} · ${profile.region.toUpperCase()}`
    : "Profile not configured";
  if (!profile.configured) return;
  $("#riot-id").value = profile.riot_id;
  $("#profile-region").value = profile.region;
  $("#primary-role").value = profile.primary_role;
  $("#secondary-roles").value = profile.secondary_roles.join(", ");
  $("#mastered-champions").value = profile.mastered_champions.join(", ");
  $("#play-preferences").value = profile.preferences.join(", ");
}

async function loadChampions() {
  const select = $("#enemy-champion");
  try {
    const data = await requestJson("/api/champions");
    const options = data.champions.map((champion) => {
      const option = document.createElement("option");
      option.value = champion.name;
      option.textContent = champion.name;
      return option;
    });
    select.replaceChildren(...options);
    const vayne = data.champions.find(
      (champion) => champion.name.toLocaleLowerCase() === "vayne"
    );
    if (vayne) select.value = vayne.name;
    select.disabled = false;
    $("#patch-label").textContent = data.patch;
    await loadCounter(new Event("submit"));
  } catch (error) {
    $("#error-message").textContent = error.message;
    $("#error-message").hidden = false;
    select.replaceChildren(new Option("Champion list unavailable", ""));
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
    const profile = await requestJson("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("#profile-status").textContent = `${profile.riot_id} · ${profile.region.toUpperCase()}`;
    setFeedback(feedback, "Profile saved on this computer.");
  } catch (requestError) {
    setFeedback(feedback, requestError.message, true);
  }
}

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => showPage(button.dataset.page));
});
$("#counter-form").addEventListener("submit", loadCounter);
$("#enemy-champion").addEventListener("change", () => loadCounter(new Event("submit")));
$("#draft-role").addEventListener("change", () => loadCounter(new Event("submit")));
$("#profile-form").addEventListener("submit", saveProfile);
setupAds();
loadChampions();
loadProfile().catch((error) => {
  $("#profile-status").textContent = "Profile unavailable";
  setFeedback($("#profile-feedback"), error.message, true);
});
