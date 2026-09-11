// static/script.js
document.addEventListener("DOMContentLoaded", function() {
  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  const grid = document.getElementById("dashboard-grid");
  // initial layout:
  const layoutEl = document.getElementById("layout-json");
  let layout = layoutEl ? JSON.parse(layoutEl.textContent) : null;

  async function loadCurrentLayoutFromAPI() {
    try {
      const res = await fetch("/api/dashboard/layouts/current");
      if (res.ok) {
        const j = await res.json();
        return j.layout_json || null;
      }
    } catch (e) { console.warn("Couldn't fetch current layout", e); }
    return null;
  }

  async function renderPanels(panels) {
    grid.innerHTML = "";
    (panels || []).forEach(p => {
      const el = document.createElement("div");
      el.className = "panel";
      el.dataset.panelId = p.id;
      el.innerHTML = `<h3>${p.id}</h3><div class="panel-body">Loading...</div>`;
      grid.appendChild(el);
      fetch(`/api/panels/${p.id}`).then(r => r.json()).then(j => {
        el.querySelector(".panel-body").textContent = JSON.stringify(j);
      }).catch(e => {
        el.querySelector(".panel-body").textContent = "Error loading";
      });
    });
  }

  (async function init() {
    if (!layout) layout = await loadCurrentLayoutFromAPI();
    if (!layout) layout = { panels: [ {id: "kpi_strip"}, {id:"stock_alerts"} ] };
    await renderPanels(layout.panels);

    // Make grid sortable (Sortables already included via CDN in base.html)
    if (typeof Sortable !== "undefined") {
      Sortable.create(grid, { animation: 150 });
    }
  })();

  // customize modal toggle
  document.getElementById("open-customize")?.addEventListener("click", () => {
    document.getElementById("modal-backdrop")?.classList.add("show");
  });
  document.getElementById("close-customize")?.addEventListener("click", () => {
    document.getElementById("modal-backdrop")?.classList.remove("show");
  });

  // Save handler
  document.querySelectorAll("#save-layout").forEach(btn => {
    btn.addEventListener("click", async () => {
      // build layout_json from DOM order (basic: store ids in order)
      const panels = Array.from(grid.children).map((child, idx) => ({
        id: child.dataset.panelId,
        position: { x: 0, y: idx, w: 1, h: 1 }
      }));
      const payload = { layout_json: { panels: panels }, version: layout.version || 1 };
      // get layout id from hidden data in page: server set via layout_id if present
      const layoutRoot = document.getElementById("dashboard-grid").closest(".grid-wrap") || document.getElementById("layout-root");
      const layoutId = document.getElementById("layout-json")?.dataset?.layoutId || null;

      // CSRF token from cookie
      const csrf = getCookie("csrf_token");

      try {
        let res;
        if (layoutId) {
          res = await fetch(`/api/dashboard/layouts/${layoutId}`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrf
            },
            body: JSON.stringify({ layout_json: payload.layout_json, version: payload.version })
          });
        } else {
          res = await fetch(`/api/dashboard/layouts`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRF-Token": csrf
            },
            body: JSON.stringify(payload)
          });
        }
        if (res.status === 200 || res.status === 201) {
          alert("Layout saved");
          const j = await res.json();
          // update current layout info
          layout = { panels: panels, version: j.version || (layout.version||1) + 1 };
          // hide modal
          document.getElementById("modal-backdrop")?.classList.remove("show");
        } else if (res.status === 409) {
          const j = await res.json();
          alert("Conflict: layout changed on server. Reload to get current version.");
        } else {
          const txt = await res.text();
          alert("Save failed: " + txt);
        }
      } catch (e) {
        alert("Save error: " + e.message);
      }
    });
  });
});
