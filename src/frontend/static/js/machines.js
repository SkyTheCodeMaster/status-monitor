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

  while (menu_list.firstChild) {
    menu_list.removeChild(menu_list.lastChild);
  }

  for (let category of category_names) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.innerText = category;
    if (selected_category != null && selected_category == category) {
      a.classList.add("is-active");
    }

    a.onclick = async function() {
      let new_params = new URLSearchParams(window.location.search);
      new_params.set("c", a.innerText);
      window.location.search = new_params.toString();
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

async function display_machines() {
  let data;
  try {
    let request = await fetch("/api/machines/get/all/");
    data = await request.json();
  } catch (e) {
    console.error(e)
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

  const stats_title = document.getElementById("stats_title");
  stats_title.innerText = format(stats_title.innerText, selected_category, online_machines, total_machines);

  const machine_grid = document.getElementById("machine_grid");

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
    console.log(machine_info);
    online_icon.style.color = machine_info["data"]["online"] ? "lime" : "red";
    online_icon.title = machine_info["data"]["online"] ? "This machine is online" : "This machine is offline";

    top_level_left_item.appendChild(machine_title);
    top_level_right_item.appendChild(online_icon);

    const hr = document.createElement("hr");
    hr.classList.add("my-1", "has-background-grey-lighter");

    // Display basic stats if stat monitor is enabled
    const stats_div = document.createElement("div");
    if (machine_info["data"]["stats"] != "invalid stats") {
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
}

async function setup() {
  await display_machines();
}

if (document.readyState == "loading") {
  document.addEventListener("DOMContentLoaded", setup);
} else {
  setup();
}