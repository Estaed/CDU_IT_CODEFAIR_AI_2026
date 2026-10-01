// The clustered workspace map (fair_turn/app/components/cluster_map.py).
// Every colour, size and URL arrives in `data`; this file carries none of its own.
// The map object lives on the parent element, so a rerun updates the source and the
// selected ring instead of rebuilding the map: the camera stays where the user left it.

const STATE_KEY = "__ftClusterMap";

function regionColour(colours) {
  const match = ["match", ["get", "region"]];
  for (const [region, colour] of Object.entries(colours.regions)) {
    match.push(region, colour);
  }
  match.push(colours.cluster);
  return match;
}

function pointRadius(layout) {
  // A community dot grows with its open jobs; the selected ring follows the same size.
  return [
    "interpolate", ["linear"], ["get", "open_jobs"],
    1, layout.point_min_radius,
    layout.point_max_jobs, layout.point_max_radius,
  ];
}

function addLayers(map, data) {
  const { colours, layout } = data;
  map.addSource("jobs", {
    type: "geojson",
    data: data.features,
    cluster: true,
    clusterRadius: layout.cluster_radius,
    clusterMaxZoom: layout.cluster_max_zoom,
    clusterProperties: { jobs: ["+", ["get", "open_jobs"]] },
  });
  map.addLayer({
    id: "clusters",
    type: "circle",
    source: "jobs",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": colours.cluster,
      "circle-opacity": layout.cluster_opacity,
      "circle-stroke-color": colours.stroke,
      "circle-stroke-width": layout.cluster_stroke,
      "circle-radius": [
        "interpolate", ["linear"], ["get", "jobs"],
        1, layout.cluster_min_radius,
        layout.cluster_max_jobs, layout.cluster_max_radius,
      ],
    },
  });
  map.addLayer({
    id: "cluster-count",
    type: "symbol",
    source: "jobs",
    filter: ["has", "point_count"],
    layout: {
      "text-field": ["to-string", ["get", "jobs"]],
      "text-font": layout.label_fonts,
      "text-size": layout.label_size,
      "text-allow-overlap": true,
    },
    paint: { "text-color": colours.label },
  });
  map.addLayer({
    id: "selected-ring",
    type: "circle",
    source: "jobs",
    filter: ["==", ["get", "community_id"], data.selected],
    paint: {
      "circle-color": "rgba(0,0,0,0)",
      "circle-stroke-color": colours.ring,
      "circle-stroke-width": layout.ring,
      "circle-radius": ["+", pointRadius(layout), layout.ring],
    },
  });
  map.addLayer({
    id: "points",
    type: "circle",
    source: "jobs",
    filter: ["!", ["has", "point_count"]],
    paint: {
      "circle-color": regionColour(colours),
      "circle-stroke-color": colours.stroke,
      "circle-stroke-width": layout.point_stroke,
      "circle-radius": pointRadius(layout),
    },
  });
  // Crews where they are this morning, drawn over the jobs and never clustered with them.
  map.addSource("crews", { type: "geojson", data: data.crews });
  map.addLayer({
    id: "crews",
    type: "circle",
    source: "crews",
    paint: {
      "circle-color": colours.crew,
      "circle-stroke-color": colours.stroke,
      "circle-stroke-width": layout.point_stroke,
      "circle-radius": layout.crew_radius,
    },
  });
  map.addLayer({
    id: "crew-labels",
    type: "symbol",
    source: "crews",
    layout: {
      "text-field": ["get", "crew_id"],
      "text-font": layout.label_fonts,
      "text-size": layout.label_size,
      "text-offset": [0, layout.crew_label_offset],
      "text-anchor": "top",
    },
    paint: {
      "text-color": colours.crew_label,
      "text-halo-color": colours.stroke,
      "text-halo-width": 1,
    },
  });
}

function update(entry, data) {
  const previous = entry.data.selected;
  entry.data = data;
  if (!entry.loaded) return; // the load handler applies the latest data
  entry.map.getSource("jobs").setData(data.features);
  entry.map.getSource("crews").setData(data.crews);
  entry.map.setFilter("selected-ring", ["==", ["get", "community_id"], data.selected]);
  // Only a changed selection moves the camera; a mode switch or a filter leaves it alone.
  if (data.selected && data.selected !== previous) {
    const target = data.features.features.find(
      (f) => f.properties.community_id === data.selected,
    );
    if (target) {
      entry.map.easeTo({
        center: target.geometry.coordinates,
        zoom: Math.max(entry.map.getZoom(), data.layout.selected_zoom),
      });
    }
  }
}

export default async function (component) {
  const { data, parentElement, setTriggerValue } = component;
  const existing = parentElement[STATE_KEY];
  if (existing) {
    update(existing, data);
    return;
  }
  const entry = { map: null, loaded: false, failed: false, data };
  parentElement[STATE_KEY] = entry;
  const fail = (reason) => {
    if (entry.failed) return;
    entry.failed = true;
    setTriggerValue("failed", String(reason).slice(0, 200));
  };

  const base = window.location.origin + "/";
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = new URL(data.urls.css, base).href;
  parentElement.appendChild(link);
  const container = document.createElement("div");
  container.id = "ft-map";
  container.style.width = "100%";
  container.style.height = data.layout.height + "px";
  parentElement.appendChild(container);

  const timer = setTimeout(() => {
    if (!entry.loaded) fail("the map did not load in time");
  }, data.layout.timeout_ms);

  let maplibregl;
  try {
    // v2 loads this module from a blob URL, so the vendored module needs a full URL.
    maplibregl = await import(new URL(data.urls.module, base).href);
  } catch (error) {
    clearTimeout(timer);
    fail("map module: " + error.message);
    return;
  }
  const lib = maplibregl.default || maplibregl;
  let map;
  try {
    map = new lib.Map({
      container,
      style: data.urls.style,
      center: data.layout.centre,
      zoom: data.layout.zoom,
      attributionControl: { compact: true },
    });
  } catch (error) {
    clearTimeout(timer);
    fail("map: " + error.message);
    return;
  }
  entry.map = map;
  map.addControl(new lib.NavigationControl({ showCompass: false }), "top-right");

  map.on("error", (event) => {
    // Before load, any error (style, sprite, source) means no usable basemap. After load a
    // single missing tile or glyph is not worth replacing a working map.
    if (entry.loaded) return;
    fail((event && event.error && event.error.message) || "map error");
  });

  map.on("load", () => {
    clearTimeout(timer);
    addLayers(map, entry.data);
    entry.loaded = true;
    update(entry, entry.data);
    container.dataset.status = "loaded";

    map.on("click", "clusters", async (event) => {
      const feature = event.features[0];
      const zoom = await map
        .getSource("jobs")
        .getClusterExpansionZoom(feature.properties.cluster_id);
      map.easeTo({ center: feature.geometry.coordinates, zoom });
    });
    map.on("click", "points", (event) => {
      setTriggerValue("picked", event.features[0].properties.community_id);
    });
    for (const layer of ["clusters", "points"]) {
      map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
    }
  });
}
