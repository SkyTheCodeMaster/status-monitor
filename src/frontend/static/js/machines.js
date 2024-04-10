let selected_machine = "";
let open_plugin_tabs = {};

function remove_children(element) {
  while (element.firstChild) {
    element.removeChild(element.lastChild);
  }
}

async function setup_category(data, search_params) {
  // First we need to get the actual category names
  let category_names = [];
  for (let entry of Object.values(data)) {
    if (!category_names.includes(entry["category"])) {
      category_names.push(entry["category"])
    }
  }
  const menu_list = document.getElementById("menu_list");

  let selected_category = search_params.get("c")

  remove_children(menu_list)

  for (let category of category_names) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.innerText = category;
    if (selected_category != null && selected_category == category) {
      a.classList.add("is-active");
    }

    a.onclick = async function() {
      const url = new URL(window.location.href);
      url.searchParams.set("c", a.innerText);
      window.history.replaceState(null, null, url);
      await display_machines();
    }

    li.appendChild(a);
    menu_list.appendChild(li);
  }

  if (selected_category == null) {
    let new_params = new URLSearchParams(window.location.search);
    new_params.set("c", category_names[0]);
    window.location.search = new_params.toString();
    await display_machines();
  }
}

async function refresh_machines(button) {
  button.classList.add("is-loading");
  button.setAttribute("disabled",true);
  await display_machines();
  button.classList.remove("is-loading");
  button.removeAttribute("disabled");
}

async function close_machine_modal() {
  let modal_machine = document.getElementById("modal_machine");
  modal_machine.classList.remove("is-active");

  const url = new URL(window.location.href);
  url.searchParams.delete("m");
  window.history.replaceState(null, null, url);
}

async function refresh_machine_modal() {
  await display_machine_modal(selected_machine);
}

async function display_machine_modal(machine_name) {
  let data = null;
  try {
    let encoded_machine_name = encodeURIComponent(machine_name).replace("%20","+");
    let request = await fetch("/api/machines/get/?name="+encoded_machine_name);
    data = await request.json();
  } catch (e) {
    console.error(e);
  }

  if (data == null) {
    return;
  }

  // Put the m param into the URL
  const url = new URL(window.location.href);
  url.searchParams.set("m", machine_name);
  window.history.replaceState(null, null, url);

  let selected_plugins = url.searchParams.get("mt")
  if (selected_plugins != null) {
    open_plugin_tabs = {};
    for (let selected_plugin of selected_plugins.split(",")) {
      open_plugin_tabs[selected_plugin] = true;
    }
  }

  let modal_machine = document.getElementById("modal_machine");
  let modal_machine_name = document.getElementById("modal_machine_name");
  let modal_machine_detailed_stats_button = document.getElementById("modal_machine_detailed_stats_button");
  let modal_machine_detailed_stats_box = document.getElementById("modal_machine_detailed_stats_box");

  modal_machine_name.innerText = data["name"]

  // Collect all of the stats elements
  if (data["data"]["stats"] == "invalid stats") {
    modal_machine_detailed_stats_button.setAttribute("disabled", true);
  } else {
    let modal_machine_detailed_stats_cpu_1m = document.getElementById("modal_machine_detailed_stats_cpu_1m");
    let modal_machine_detailed_stats_cpu_5m = document.getElementById("modal_machine_detailed_stats_cpu_5m");
    let modal_machine_detailed_stats_cpu_15m = document.getElementById("modal_machine_detailed_stats_cpu_15m");

    let modal_machine_detailed_stats_ram_percent = document.getElementById("modal_machine_detailed_stats_ram_percent");
    let modal_machine_detailed_stats_ram_free = document.getElementById("modal_machine_detailed_stats_ram_free");
    let modal_machine_detailed_stats_ram_used = document.getElementById("modal_machine_detailed_stats_ram_used");
    let modal_machine_detailed_stats_ram_total = document.getElementById("modal_machine_detailed_stats_ram_total");

    let modal_machine_detailed_stats_disk_percent = document.getElementById("modal_machine_detailed_stats_disk_percent");
    let modal_machine_detailed_stats_disk_free = document.getElementById("modal_machine_detailed_stats_disk_free");
    let modal_machine_detailed_stats_disk_used = document.getElementById("modal_machine_detailed_stats_disk_used");
    let modal_machine_detailed_stats_disk_total = document.getElementById("modal_machine_detailed_stats_disk_total");

    let modal_machine_detailed_stats_network_current_up = document.getElementById("modal_machine_detailed_stats_network_current_up");
    let modal_machine_detailed_stats_network_current_down = document.getElementById("modal_machine_detailed_stats_network_current_down");
    let modal_machine_detailed_stats_network_5m_up = document.getElementById("modal_machine_detailed_stats_network_5m_up");
    let modal_machine_detailed_stats_network_5m_down = document.getElementById("modal_machine_detailed_stats_network_5m_down");

    let modal_machine_detailed_stats_boot_time = document.getElementById("modal_machine_detailed_stats_boot_time");

    let cpu = data["data"]["stats"]["cpu"];
    modal_machine_detailed_stats_cpu_1m.innerText = cpu["1m"];
    modal_machine_detailed_stats_cpu_5m.innerText = cpu["5m"];
    modal_machine_detailed_stats_cpu_15m.innerText = cpu["15m"];

    let ram = data["data"]["stats"]["ram"];
    let ram_percent = ((ram["used"]/ram["total"])*100).toFixed(1);
    modal_machine_detailed_stats_ram_percent.innerText = ram_percent+"%";
    modal_machine_detailed_stats_ram_free.innerText = format_bytes(ram["free"]);
    modal_machine_detailed_stats_ram_used.innerText = format_bytes(ram["used"]);
    modal_machine_detailed_stats_ram_total.innerText = format_bytes(ram["total"]);

    let disk = data["data"]["stats"]["disk"];
    let disk_percent = ((disk["used"]/disk["total"])*100).toFixed(1);
    modal_machine_detailed_stats_disk_percent.innerText = disk_percent+"%";
    modal_machine_detailed_stats_disk_free.innerText = format_bytes(disk["free"]);
    modal_machine_detailed_stats_disk_used.innerText = format_bytes(disk["used"]);
    modal_machine_detailed_stats_disk_total.innerText = format_bytes(disk["total"]);

    let internet = data["data"]["stats"]["internet"];
    modal_machine_detailed_stats_network_current_up.innerText = format_bytes_per_second(internet["current"]["outgoing"]);
    modal_machine_detailed_stats_network_current_down.innerText = format_bytes_per_second(internet["current"]["incoming"]);
    modal_machine_detailed_stats_network_5m_up.innerText = format_bytes_per_second(internet["5m"]["outgoing"]);
    modal_machine_detailed_stats_network_5m_down.innerText = format_bytes_per_second(internet["5m"]["incoming"]);

    let boot_time_utc = data["data"]["stats"]["boot_time"];
    let boot_time_date = new Date(boot_time_utc*1000);
    modal_machine_detailed_stats_boot_time.innerText = boot_time_date.toString();
  }

  if (open_plugin_tabs["basicstats"]) {
    modal_machine_detailed_stats_box.style.display = "";
  }

  // Setup default open of stats
  modal_machine_detailed_stats_button.onclick = function() {
    toggle_modal_box("modal_machine_detailed_stats_box");
    open_plugin_tabs["basicstats"] = modal_machine_detailed_stats_box.style.display == "";
    const url = new URL(window.location.href);
    let selected_plugins = Object.keys(open_plugin_tabs).filter(k => open_plugin_tabs[k])
    if (selected_plugins.length == 0) {
      url.searchParams.delete("mt");
    } else {
      url.searchParams.set("mt", selected_plugins.join(","));
    }
    window.history.replaceState(null, null, url);
  }

  // Now start adding plugins
  let modal_machine_plugin_div = document.getElementById("modal_machine_plugin_div");
  remove_children(modal_machine_plugin_div);
  let plugin_elements = await run_plugins(data["data"]["extras"]);

  for (let [name,element] of Object.entries(plugin_elements)) {
    // Create a button and set it up
    const plugin_id = make_id(12);
    const plugin_name = (" "+name).slice(1)
    const button = document.createElement("button");
    button.classList.add("button","is-fullwidth","mt-2");
    button.id = format("modal_machine_plugin_button_{0}", plugin_id);
    element.id = format("modal_machine_plugin_box_{0}", plugin_id);
    button.onclick = function() { 
      toggle_modal_box("modal_machine_plugin_box_"+plugin_id);
      open_plugin_tabs[plugin_name] = element.style.display == "";

      const url = new URL(window.location.href);
      let selected_plugins = Object.keys(open_plugin_tabs).filter(k => open_plugin_tabs[k])
      if (selected_plugins.length == 0) {
        url.searchParams.delete("mt");
      } else {
        url.searchParams.set("mt", selected_plugins.join(","));
      }
      window.history.replaceState(null, null, url);
    };
    button.innerText = to_title_case(name);

    if (open_plugin_tabs[plugin_name]) {
      element.style.display = "";
    } else {
      open_plugin_tabs[plugin_name] = false; // Explicity add false.
    }

    modal_machine_plugin_div.appendChild(button);
    modal_machine_plugin_div.appendChild(element);
  }

  modal_machine.classList.add("is-active");
}

async function toggle_modal_box(element_id) {
  const element = document.getElementById(element_id);
  if (element.style.display === "none") {
    element.style.display = "";
  } else {
    element.style.display = "none";
  }
}

async function display_machines() {
  let data;
  try {
    let request = await fetch("/api/machines/get/all/");
    data = await request.json();
  } catch (e) {
    console.error(e);
  }

  let search_params = new URLSearchParams(window.location.search);

  await setup_category(data, search_params);

  let selected_category = search_params.get("c");
  let selected_machines = {};
  let online_machines = 0, total_machines = 0;

  for (let [name, machine_info] of Object.entries(data)) {
    if (machine_info["category"] == selected_category) {
      selected_machines[name] = machine_info;
      total_machines++;
      if (machine_info["data"]["online"]) online_machines++;
    }
  }

  // Sort the machines by name
  selected_machines = Object.keys(selected_machines).sort().reduce(
    (obj, key) => { 
      obj[key] = selected_machines[key]; 
      return obj;
    }, 
    {}
  );

  const stats_title = document.getElementById("stats_title");
  stats_title.innerText = format(stats_title.getAttribute("text"), selected_category, online_machines, total_machines);

  const machine_grid = document.getElementById("machine_grid");

  while (machine_grid.firstChild) {
    machine_grid.removeChild(machine_grid.lastChild);
  }

  for (let [name, machine_info] of Object.entries(selected_machines)) {
    const cell = document.createElement("div");
    cell.classList.add("cell", "box", "has-background-grey", "is-col-span-2");
    cell.style.width = "fit-content";
    cell.style.height = "fit-content";

    const top_level = document.createElement("div");
    top_level.classList.add("level", "mb-0");
    const top_level_left = document.createElement("div");
    top_level_left.classList.add("level-left");
    const top_level_right = document.createElement("div");
    top_level_right.classList.add("level-right");
    const top_level_left_item = document.createElement("div");
    top_level_left_item.classList.add("level-item");
    const top_level_right_item = document.createElement("div");
    top_level_right_item.classList.add("level-item", "ml-4");

    top_level.appendChild(top_level_left);
    top_level.appendChild(top_level_right);
    top_level_left.appendChild(top_level_left_item);
    top_level_right.appendChild(top_level_right_item);


    const machine_title = document.createElement("h1");
    machine_title.innerText = name;
    machine_title.classList.add("title", "is-4");
    machine_title.style.color = "white";

    const online_icon = document.createElement("iconify-icon");
    online_icon.setAttribute("icon", "ph:globe");
    online_icon.setAttribute("width", "2em");
    online_icon.setAttribute("height", "2em");
    online_icon.style.color = machine_info["data"]["online"] ? "lime" : "red";
    online_icon.title = machine_info["data"]["online"] ? "This machine is online" : "This machine is offline";

    top_level_left_item.appendChild(machine_title);
    top_level_right_item.appendChild(online_icon);

    const hr = document.createElement("hr");
    hr.classList.add("my-1", "has-background-grey-lighter");

    // Display basic stats if stat monitor is enabled
    const stats_div = document.createElement("div");
    if (machine_info["data"]["stats"] != "invalid stats" && machine_info["data"]["stats"] != null) {
      const stats_level = document.createElement("div");
      stats_level.classList.add("level","m-0");

      // CPU
      const cpu = machine_info["data"]["stats"]["cpu"];
      const cpu_level_item = document.createElement("div");
      cpu_level_item.classList.add("level-item");
      const cpu_icon = document.createElement("iconify-icon");
      cpu_icon.setAttribute("icon","ph:cpu");
      cpu_icon.setAttribute("width", "1.5em");
      cpu_icon.setAttribute("height", "1.5em");
      const cpu_text = document.createElement("p");
      cpu_text.innerText = cpu["1m"];
      cpu_text.style.color = "white";
      cpu_icon.style.color = "white";
      cpu_level_item.appendChild(cpu_icon);
      cpu_level_item.appendChild(cpu_text);
      stats_level.appendChild(cpu_level_item);

      // RAM
      const ram = machine_info["data"]["stats"]["ram"];
      const ram_level_item = document.createElement("div");
      ram_level_item.classList.add("level-item");
      const ram_icon = document.createElement("iconify-icon");
      ram_icon.setAttribute("icon","ph:memory");
      ram_icon.setAttribute("width", "1.5em");
      ram_icon.setAttribute("height", "1.5em");

      let percent_ram_used = +((ram["used"]/ram["total"])*100).toFixed(1);
      const ram_text = document.createElement("p");
      ram_text.innerText = percent_ram_used + "%";

      let percent_ram_used_hover = format("{0}/{1}", format_bytes(ram["used"], 1), format_bytes(ram["total"], 1));
      ram_text.title = percent_ram_used_hover;
      ram_icon.title = percent_ram_used_hover;

      if (percent_ram_used >= 85) {
        ram_icon.style.color = "red";
        ram_text.style.color = "red";
      } else if (percent_ram_used >= 50) {
        ram_icon.style.color = "yellow";
        ram_text.style.color = "yellow";
      } else {
        ram_icon.style.color = "white";
        ram_text.style.color = "white";
      }

      ram_level_item.appendChild(ram_icon);
      ram_level_item.appendChild(ram_text);
      stats_level.appendChild(ram_level_item);

      // Disk
      const disk = machine_info["data"]["stats"]["disk"];
      const disk_level_item = document.createElement("div");
      disk_level_item.classList.add("level-item");
      const disk_icon = document.createElement("iconify-icon");
      disk_icon.setAttribute("icon","carbon:vmdk-disk");
      disk_icon.setAttribute("width", "1.5em");
      disk_icon.setAttribute("height", "1.5em");

      let percent_disk_used = +((disk["used"]/disk["total"])*100).toFixed(1);
      const disk_text = document.createElement("p");
      disk_text.innerText = percent_disk_used + "%";

      let percent_disk_used_hover = format("{0}/{1}", format_bytes(disk["used"]), format_bytes(disk["total"]));
      disk_text.title = percent_disk_used_hover;
      disk_icon.title = percent_disk_used_hover;

      if (percent_disk_used >= 85) {
        disk_icon.style.color = "red";
        disk_text.style.color = "red";
      } else if (percent_disk_used >= 50) {
        disk_icon.style.color = "yellow";
        disk_text.style.color = "yellow";
      } else {
        disk_icon.style.color = "white";
        disk_text.style.color = "white";
      }

      disk_level_item.appendChild(disk_icon);
      disk_level_item.appendChild(disk_text);
      stats_level.appendChild(disk_level_item);

      // Open modal button
      const open_level_item = document.createElement("div");
      open_level_item.classList.add("level-item");
      const open_button = document.createElement("button");

      const copied_name = (" " + name).slice(1);
      open_button.onclick = async function() {
        selected_machine = copied_name;
        await display_machine_modal(copied_name);
      }

      const open_icon = document.createElement("iconify-icon");
      open_icon.setAttribute("icon","majesticons:open");
      open_icon.setAttribute("width","1.5em");
      open_icon.setAttribute("height","1.5em");
      open_icon.style.color = "white";
      open_icon.title = "Open details";

      open_button.appendChild(open_icon);
      open_level_item.appendChild(open_button);
      stats_level.appendChild(open_level_item);

      stats_div.appendChild(stats_level);
    } else {
      const p = document.createElement("p");
      p.innerText = "Machine has invalid stats.";
      p.style.color = "white";
      stats_div.appendChild(p);
    }

    cell.appendChild(top_level);
    cell.append(hr);
    cell.append(stats_div);
    
    machine_grid.appendChild(cell);
  }

  let preview_machine = search_params.get("m");
  if (preview_machine != null) {
    await display_machine_modal(preview_machine);
  }
}

async function setup() {
  await display_machines();
  setInterval(async function() {
    let button = document.getElementById("refresh_machines_button");
    await refresh_machines(button);
  }, 60000);
}

if (document.readyState == "loading") {
  document.addEventListener("DOMContentLoaded", setup);
} else {
  setup();
}