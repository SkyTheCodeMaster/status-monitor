let ALL_PLUGINS = [];

async function run_plugins(extras) {
  // feed in extras object
  // return Name: HTMLElement
  let out = {};
  for (let plugin of ALL_PLUGINS) {
    let plugin_out = await plugin(extras);
    if (plugin_out != null) {
      let pretty_name = plugin.name.slice(0,-7)
      out[pretty_name] = plugin_out;
    }
  }
  return out;
}

// Take in the entire extras dictionary,
// and is expected to return an HTML element
// of a box with data inside.
// Additionally, the modal itself hands out element IDs, instead of setting them here.
async function example_plugin(extras) {
  return null;
}
ALL_PLUGINS.push(example_plugin)

// xmrig plugin
async function xmrig_plugin(extras) {
  if (extras["xmrig"] == null) {
    return null;
  }

  const xmrig = extras["xmrig"]

  const top_box = document.createElement("div");
  top_box.classList.add("box");
  // All of these should start out hidden.
  top_box.style.display = "none";
  
  const hashrate = xmrig["hashrate"];

  const hashrate_level = document.createElement("div");
  hashrate_level.classList.add("level");

  const hashrate_level_item_icon = document.createElement("div");
  hashrate_level_item_icon.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const hashrate_level_item_icon_p = document.createElement("p");
  hashrate_level_item_icon_p.innerHTML = "<b>Hashrate</b>";

  const hashrate_level_item_icon_iconify = document.createElement("iconify-icon");
  hashrate_level_item_icon_iconify.setAttribute("icon", "bitcoin-icons:mining-outline");

  hashrate_level_item_icon.appendChild(hashrate_level_item_icon_p);
  hashrate_level_item_icon.appendChild(hashrate_level_item_icon_iconify);
  
  hashrate_level.appendChild(hashrate_level_item_icon);

  // Current

  const hashrate_level_item_current = document.createElement("div");
  hashrate_level_item_current.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const hashrate_level_item_current_p = document.createElement("p");
  hashrate_level_item_current_p.innerHTML = "<b>Now</b>";

  const hashrate_level_item_current_text = document.createElement("p");
  hashrate_level_item_current_text.innerText = format_hashes_per_second(hashrate["current"])

  hashrate_level_item_current.appendChild(hashrate_level_item_current_p);
  hashrate_level_item_current.appendChild(hashrate_level_item_current_text);
  
  hashrate_level.appendChild(hashrate_level_item_current);

  const hashrate_level_item_1m = document.createElement("div");
  hashrate_level_item_1m.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const hashrate_level_item_1m_p = document.createElement("p");
  hashrate_level_item_1m_p.innerHTML = "<b>1m</b>";

  const hashrate_level_item_1m_text = document.createElement("p");
  hashrate_level_item_1m_text.innerText = format_hashes_per_second(hashrate["1m"])

  hashrate_level_item_1m.appendChild(hashrate_level_item_1m_p);
  hashrate_level_item_1m.appendChild(hashrate_level_item_1m_text);
  
  hashrate_level.appendChild(hashrate_level_item_1m);

  const hashrate_level_item_15m = document.createElement("div");
  hashrate_level_item_15m.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const hashrate_level_item_15m_p = document.createElement("p");
  hashrate_level_item_15m_p.innerHTML = "<b>15m</b>";

  const hashrate_level_item_15m_text = document.createElement("p");
  hashrate_level_item_15m_text.innerText = format_hashes_per_second(hashrate["15m"])

  hashrate_level_item_15m.appendChild(hashrate_level_item_15m_p);
  hashrate_level_item_15m.appendChild(hashrate_level_item_15m_text);
  
  hashrate_level.appendChild(hashrate_level_item_15m);

  const details_level = document.createElement("div");
  details_level.classList.add("level");

  const details_level_item_worker_id = document.createElement("div");
  details_level_item_worker_id.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const details_level_item_worker_id_title = document.createElement("p");
  details_level_item_worker_id_title.innerHTML = "<b>Worker ID</b>";
  const details_level_item_worker_id_text = document.createElement("p");
  details_level_item_worker_id_text.innerText = xmrig["worker_id"];

  details_level_item_worker_id.appendChild(details_level_item_worker_id_title);
  details_level_item_worker_id.appendChild(details_level_item_worker_id_text);

  details_level.appendChild(details_level_item_worker_id);

  const details_level_item_uptime = document.createElement("div");
  details_level_item_uptime.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const details_level_item_uptime_title = document.createElement("p");
  details_level_item_uptime_title.innerHTML = "<b>Uptime</b>";
  const details_level_item_uptime_text = document.createElement("p");
  details_level_item_uptime_text.innerText = parse_seconds(xmrig["uptime"]);

  details_level_item_uptime.appendChild(details_level_item_uptime_title);
  details_level_item_uptime.appendChild(details_level_item_uptime_text);

  details_level.appendChild(details_level_item_uptime);

  const details_level_item_version = document.createElement("div");
  details_level_item_version.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const details_level_item_version_title = document.createElement("p");
  details_level_item_version_title.innerHTML = "<b>Version</b>";
  const details_level_item_version_text = document.createElement("p");
  details_level_item_version_text.innerText = xmrig["version"];

  details_level_item_version.appendChild(details_level_item_version_title);
  details_level_item_version.appendChild(details_level_item_version_text);

  details_level.appendChild(details_level_item_version);

  // Shares
  const shares = xmrig["shares"]

  const shares_level = document.createElement("div");
  shares_level.classList.add("level");

  const shares_level_item_total_shares = document.createElement("div");
  shares_level_item_total_shares.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_level_item_total_shares_title = document.createElement("p");
  shares_level_item_total_shares_title.innerHTML = "<b>Shares</b>";
  const shares_level_item_total_shares_text = document.createElement("p");
  shares_level_item_total_shares_text.innerText = shares["total"];

  shares_level_item_total_shares.appendChild(shares_level_item_total_shares_title);
  shares_level_item_total_shares.appendChild(shares_level_item_total_shares_text);

  shares_level.appendChild(shares_level_item_total_shares);

  const shares_level_item_percent_good_shares = document.createElement("div");
  shares_level_item_percent_good_shares.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_level_item_percent_good_shares_title = document.createElement("p");
  shares_level_item_percent_good_shares_title.innerHTML = "<b>Percent</b>";
  shares_level_item_percent_good_shares_title.title = "Percent of good shares";
  const shares_level_item_percent_good_shares_text = document.createElement("p");
  let percent_good_shares = ((shares["good"]/shares["total"])*100).toFixed(1)
  shares_level_item_percent_good_shares_text.innerText = percent_good_shares + "%";
  shares_level_item_percent_good_shares_text.title = "Percent of good shares";

  shares_level_item_percent_good_shares.appendChild(shares_level_item_percent_good_shares_title);
  shares_level_item_percent_good_shares.appendChild(shares_level_item_percent_good_shares_text);

  shares_level.appendChild(shares_level_item_percent_good_shares);

  const shares_level_item_good_shares = document.createElement("div");
  shares_level_item_good_shares.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_level_item_good_shares_title = document.createElement("p");
  shares_level_item_good_shares_title.innerHTML = "<b>Good</b>";
  const shares_level_item_good_shares_text = document.createElement("p");
  shares_level_item_good_shares_text.innerText = shares["good"];

  shares_level_item_good_shares.appendChild(shares_level_item_good_shares_title);
  shares_level_item_good_shares.appendChild(shares_level_item_good_shares_text);

  shares_level.appendChild(shares_level_item_good_shares);

  const shares_level_item_bad_shares = document.createElement("div");
  shares_level_item_bad_shares.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_level_item_bad_shares_title = document.createElement("p");
  shares_level_item_bad_shares_title.innerHTML = "<b>Bad</b>";
  const shares_level_item_bad_shares_text = document.createElement("p");
  let bad_shares = shares["total"]-shares["good"];
  shares_level_item_bad_shares_text.innerText = bad_shares;

  shares_level_item_bad_shares.appendChild(shares_level_item_bad_shares_title);
  shares_level_item_bad_shares.appendChild(shares_level_item_bad_shares_text);

  shares_level.appendChild(shares_level_item_bad_shares);

  const shares_extended_level = document.createElement("div");
  shares_extended_level.classList.add("level");

  const shares_extended_level_item_average_time = document.createElement("div");
  shares_extended_level_item_average_time.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_extended_level_item_average_time_title = document.createElement("p");
  shares_extended_level_item_average_time_title.innerHTML = "<b>Average Time</b>";
  shares_extended_level_item_average_time_title.title = "Average time between share submission";
  const shares_extended_level_item_average_time_text = document.createElement("p");
  shares_extended_level_item_average_time_text.innerText = parse_seconds(shares["avg_time_ms"]/1000, 2);
  shares_extended_level_item_average_time_text.title = "Average time between share submission";

  shares_extended_level_item_average_time.appendChild(shares_extended_level_item_average_time_title);
  shares_extended_level_item_average_time.appendChild(shares_extended_level_item_average_time_text);

  shares_extended_level.appendChild(shares_extended_level_item_average_time);

  const shares_extended_level_item_total_hashes = document.createElement("div");
  shares_extended_level_item_total_hashes.classList.add(
    "is-flex", // jesus take the wheel
    "is-flex-direction-column",
    "is-align-items-center",
    "is-justify-content-center",
    "level-item"
  )

  const shares_extended_level_item_total_hashes_title = document.createElement("p");
  shares_extended_level_item_total_hashes_title.innerHTML = "<b>Total Hashes</b>";
  shares_extended_level_item_total_hashes_title.title = shares["hashes_total"];
  const shares_extended_level_item_total_hashes_text = document.createElement("p");
  shares_extended_level_item_total_hashes_text.innerText = format_human(shares["hashes_total"]);
  shares_extended_level_item_total_hashes_text.title = shares["hashes_total"];

  shares_extended_level_item_total_hashes.appendChild(shares_extended_level_item_total_hashes_title);
  shares_extended_level_item_total_hashes.appendChild(shares_extended_level_item_total_hashes_text);

  shares_extended_level.appendChild(shares_extended_level_item_total_hashes);

  top_box.appendChild(hashrate_level);
  top_box.appendChild(details_level);
  top_box.appendChild(shares_level);
  top_box.appendChild(shares_extended_level);

  return top_box
}
ALL_PLUGINS.push(xmrig_plugin)