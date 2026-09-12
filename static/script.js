// static/script.js

document.addEventListener("DOMContentLoaded", function() {
  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }

  const grid = document.getElementById("dashboard-grid");
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
    if (!grid) return;
    grid.innerHTML = "";
    (panels || []).forEach(p => {
      const el = document.createElement("div");
      el.className = "panel";
      el.dataset.panelId = p.id;
      el.innerHTML = `<h3>${p.id}</h3><div class="panel-body">Loading...</div>`;
      grid.appendChild(el);
      fetch(`/api/panels/${p.id}`).then(r => r.json()).then(j => {
        el.querySelector(".panel-body").textContent = JSON.stringify(j.data || j);
      }).catch(e => {
        el.querySelector(".panel-body").textContent = "Error loading";
      });
    });
  }

  (async function init() {
    if (!layout) layout = await loadCurrentLayoutFromAPI();
    if (!layout) layout = { panels: [ {id: "kpi_strip"}, {id:"stock_alerts"} ] };
    await renderPanels(layout.panels);

    if (typeof Sortable !== "undefined" && grid) {
      Sortable.create(grid, { animation: 150 });
    }
  })();

  document.getElementById("open-customize")?.addEventListener("click", () => {
    document.getElementById("modal-backdrop")?.classList.add("show");
  });
  document.getElementById("close-customize")?.addEventListener("click", () => {
    document.getElementById("modal-backdrop")?.classList.remove("show");
  });

  document.querySelectorAll("#save-layout").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!grid) return;
      const panels = Array.from(grid.children).map((child, idx) => ({
        id: child.dataset.panelId,
        position: { x: 0, y: idx, w: 1, h: 1 }
      }));
      const payload = { layout_json: { panels: panels }, version: layout.version || 1 };
      const csrf = getCookie("csrf_token");
      // find layout id if included in layout-json element dataset
      const layoutId = document.getElementById("layout-json")?.dataset?.layoutId || null;
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
          layout = { panels: panels, version: j.version || (layout.version||1) + 1 };
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
