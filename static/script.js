// ============ DASHBOARD PANEL MANAGEMENT ============
document.addEventListener("DOMContentLoaded", function () {
  const panelsDiv = document.getElementById("panels");
  let layout = window.INITIAL_LAYOUT || { panels: [] };

  function render() {
    if (!panelsDiv) return;
    panelsDiv.innerHTML = "";
    layout.panels.forEach((p, i) => {
      const el = document.createElement("div");
      el.className = "panel";
      el.dataset.panelId = p.id;
      el.innerHTML = `<h3>${p.id}</h3><pre>${JSON.stringify(p.position)}</pre>
        <button data-move-up="${i}">↑</button>
        <button data-move-down="${i}">↓</button>`;
      panelsDiv.appendChild(el);
    });
  }

  function move(index, dir) {
    const newIndex = index + dir;
    if (newIndex < 0 || newIndex >= layout.panels.length) return;
    const [item] = layout.panels.splice(index, 1);
    layout.panels.splice(newIndex, 0, item);
    render();
  }

  if (panelsDiv) {
    panelsDiv.addEventListener("click", (e) => {
      const up = e.target.getAttribute("data-move-up");
      const down = e.target.getAttribute("data-move-down");
      if (up !== null) move(parseInt(up, 10), -1);
      if (down !== null) move(parseInt(down, 10), 1);
    });
  }

  const customizeBtn = document.getElementById("customize");
  if (customizeBtn) {
    customizeBtn.addEventListener("click", async () => {
      // save as user's layout (GET current to know if there is an id)
      const resp = await fetch("/api/dashboard/layouts/current");
      let data = await resp.json();
      let payload = { layout_json: layout };
      if (resp.status === 200 && data.id) {
        // update existing layout (we need current version)
        payload.version = data.version;
        const putResp = await fetch(`/api/dashboard/layouts/${data.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (putResp.status === 200) {
          alert("Layout saved");
        } else if (putResp.status === 409) {
          const body = await putResp.json();
          alert("Save failed: stale layout. Reloading current layout.");
          // reload current layout from server
          const r2 = await fetch("/api/dashboard/layouts/current");
          const updated = await r2.json();
          layout = updated.layout_json;
          render();
        } else {
          const b = await putResp.json();
          alert("Save failed: " + JSON.stringify(b));
        }
      } else {
        // create new layout
        const postResp = await fetch("/api/dashboard/layouts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (postResp.status === 201) {
          alert("Layout created");
        } else {
          const b = await postResp.json();
          alert("Create failed: " + JSON.stringify(b));
        }
      }
    });
  }

  render();
});

// ============ FILTER & PAGE NAVIGATION ============
function initFilterButtons() {
  const filterBtns = document.querySelectorAll('[data-filter]');
  const tableRows = document.querySelectorAll('[data-status]');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filterValue = btn.getAttribute('data-filter');
      
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      tableRows.forEach(row => {
        if (filterValue === 'all' || row.getAttribute('data-status') === filterValue) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  });
}

function initPageNavigation() {
  const navLinks = document.querySelectorAll('[data-go]');
  
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = link.getAttribute('data-go');
      const pages = document.querySelectorAll('.page');
      
      pages.forEach(page => page.classList.remove('active'));
      const targetPage = document.getElementById(`page-${target}`);
      if (targetPage) {
        targetPage.classList.add('active');
      }
    });
  });
}

// ============ WEBSOCKET LAYER (PLACEHOLDER) ============
function initWebSocket() {
  // Placeholder for WebSocket connection to backend
  // For live channel messages and alert updates
  // To be implemented in Phase 6
}

// ============ INITIALIZATION ============
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initFilterButtons();
    initPageNavigation();
    initWebSocket();
  });
} else {
  initFilterButtons();
  initPageNavigation();
  initWebSocket();
}
