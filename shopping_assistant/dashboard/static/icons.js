(() => {
  const icons = {
    "arrow-down-up":
      '<path d="M7 3v18"/><path d="m3 7 4-4 4 4"/><path d="M17 21V3"/><path d="m13 17 4 4 4-4"/>',
    "arrow-left": '<path d="M19 12H5"/><path d="m11 18-6-6 6-6"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    armchair:
      '<path d="M6 12V7a4 4 0 0 1 8 0v5"/><path d="M18 12V8a2 2 0 0 1 4 0v9H2V8a2 2 0 0 1 4 0v4"/><path d="M4 17v3"/><path d="M20 17v3"/>',
    "bell-off":
      '<path d="m3 3 18 18"/><path d="M10.3 4.2A5 5 0 0 1 17 9v4l2 3H9"/><path d="M7 9v4l-2 3h6"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    "bell-plus":
      '<path d="M10 5a5 5 0 0 1 9 3v4l2 3H4l2-3V8a5 5 0 0 1 4-4"/><path d="M12 20a2 2 0 0 0 4 0"/><path d="M4 5h6"/><path d="M7 2v6"/>',
    "bell-ring":
      '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/><path d="M2 8c0-2 1-4 3-5"/><path d="M22 8c0-2-1-4-3-5"/>',
    "bookmark-plus":
      '<path d="M19 21 12 17 5 21V5a2 2 0 0 1 2-2h6"/><path d="M17 3v6"/><path d="M14 6h6"/>',
    database:
      '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "external-link":
      '<path d="M14 4h6v6"/><path d="m10 14 10-10"/><path d="M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"/>',
    lamp:
      '<path d="M8 2h8l3 8H5l3-8Z"/><path d="M12 10v8"/><path d="M9 22h6"/><path d="M10 18h4"/>',
    "layout-grid":
      '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "line-chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-8"/>',
    "list-plus": '<path d="M3 6h11"/><path d="M3 12h8"/><path d="M3 18h8"/><path d="M18 14v8"/><path d="M14 18h8"/>',
    "package-search":
      '<path d="m7.5 4.3 4.5 2.6 4.5-2.6"/><path d="M21 8.2v7.6L12 21 3 15.8V8.2L12 3l9 5.2Z"/><path d="M12 7v5"/><circle cx="16.5" cy="16.5" r="2.5"/><path d="m19 19 2 2"/>',
    plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
    radar:
      '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="M12 12 19 5"/><path d="M12 12h9"/>',
    refrigerator:
      '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M6 10h12"/><path d="M10 6h.01"/><path d="M10 14h.01"/>',
    "refresh-cw":
      '<path d="M21 12a9 9 0 0 1-15.5 6.2"/><path d="M3 12A9 9 0 0 1 18.5 5.8"/><path d="M18 2v4h4"/><path d="M6 22v-4H2"/>',
    scan:
      '<path d="M7 3H5a2 2 0 0 0-2 2v2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M17 21h2a2 2 0 0 0 2-2v-2"/>',
    "scan-search":
      '<path d="M7 3H5a2 2 0 0 0-2 2v2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M17 21h2a2 2 0 0 0 2-2v-2"/><circle cx="11" cy="11" r="3"/><path d="m14 14 3 3"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "search-x":
      '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/><path d="m9 9 4 4"/><path d="m13 9-4 4"/>',
    store:
      '<path d="M4 10h16l-1.5-6h-13L4 10Z"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/><path d="M4 10c0 2 4 2 4 0 0 2 4 2 4 0 0 2 4 2 4 0 0 2 4 2 4 0"/>',
    "triangle-alert":
      '<path d="M12 3 22 20H2L12 3Z"/><path d="M12 9v5"/><path d="M12 17h.01"/>',
    tv: '<rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
  };

  const renderFallbackIcons = () => {
    document.querySelectorAll("i[data-lucide]").forEach((node) => {
      const name = node.getAttribute("data-lucide");
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 24 24");
      svg.setAttribute("fill", "none");
      svg.setAttribute("stroke", "currentColor");
      svg.setAttribute("stroke-width", "2");
      svg.setAttribute("stroke-linecap", "round");
      svg.setAttribute("stroke-linejoin", "round");
      svg.setAttribute("aria-hidden", "true");
      svg.innerHTML = icons[name] || icons.search;
      node.replaceWith(svg);
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
      window.lucide.createIcons();
      window.setTimeout(renderFallbackIcons, 0);
      return;
    }

    renderFallbackIcons();
  });
})();
