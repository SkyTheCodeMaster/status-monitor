//const { BulmaTagsInput } = require("/js/vendored/bulma-tagsinput.min.js");

require.config({ paths: { 'vs': '/js/vendored/monaco-0.47.0/vs' }});
let current_editor;
let g_monaco;

function remove_children(element) {
  while (element.firstChild) {
    element.removeChild(element.lastChild);
  }
}

async function setup_menu(data) {
  // First we need to get the actual machine names
  let unordered_machine_names = {}; // category: name
  for (let entry of Object.values(data)) {
    if (unordered_machine_names[entry["category"]] == null) {
      unordered_machine_names[entry["category"]] = [];
    }
    unordered_machine_names[entry["category"]].push(entry["name"]);
  }

  for (let [k,v] of Object.entries(unordered_machine_names)) {
    v.sort();
  }

  const machine_names = Object.keys(unordered_machine_names).sort().reverse().reduce(
    (obj, key) => { 
      obj[key] = unordered_machine_names[key]; 
      return obj;
    }, 
    {}
  );

  const menu_list = document.getElementById("menu_list");
  
  const url = new URL(window.location.href);
  let selected_machine = url.searchParams.get("m");

  if (selected_machine == null) {
    const url = new URL(window.location.href);
    let first_key = Object.keys(machine_names)[0]
    url.searchParams.set("m", machine_names[first_key][0]);
    selected_machine = machine_names[first_key][0];
    window.history.replaceState(null, null, url);
  }

  remove_children(menu_list)

  for (let [category_name, names] of Object.entries(machine_names)) {
    const p = document.createElement("p");
    p.classList.add("menu-label");
    p.innerText = category_name;
    const ul = document.createElement("ul");
    ul.classList.add("menu-list");

    for (let machine_name of names) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.innerText = machine_name;
      if (selected_machine != null && selected_machine == machine_name) {
        a.classList.add("is-active");
      }
  
      a.onclick = async function() {
        const url = new URL(window.location.href);
        url.searchParams.set("m", a.innerText);
        window.history.replaceState(null, null, url);
        await edit_machine();
        await setup_menu(data);
      }
  
      ul.appendChild(a);
    }
    menu_list.appendChild(p);
    menu_list.appendChild(ul);
  }
}

async function edit_machine() {
  const url = new URL(window.location.href)
  let selected_machine = url.searchParams.get("m");

  let data;
  try {
    let request = await fetch("/api/machines/info/?name="+encodeURIComponent(selected_machine).replace("%20","+"));
    data = await request.json();
  } catch (e) {
    console.error(e);
  }

  const machine_name_title = document.getElementById("machine_name_title");
  machine_name_title.innerText = format(machine_name_title.getAttribute("text"), data["name"], data["category"]);

  // Initialize the Monaco Editor.
  let editor_box = document.getElementById("monaco_editor");
  let pretty_json = JSON.stringify(data["extra_config"], null, 2);

  require(["vs/editor/editor.main"], function() {
    g_monaco = monaco;

    if (current_editor != null) {
      current_editor.dispose();
    }

    current_editor = monaco.editor.create(editor_box, {
      "language": "json",
      "value" : pretty_json
    });

    current_editor.getModel().updateOptions({ "tabSize": 2});
  });

  const input_category = document.getElementById("input_category");
  const input_stats_enabled = document.getElementById("input_stats_enabled");
  const plugins_tags = document.getElementById("plugins_tags");
  const scripts_tags = document.getElementById("scripts_tags");

  let scripts_data;
  try {
    let request = await fetch("/api/machines/get/scripts/");
    scripts_data = await request.json();
  } catch (e) {
    console.error(e);
  }

  input_category.value = data["category"];
  input_stats_enabled.checked = data["stats_enabled"];

  if (plugins_tags.BulmaTagsInput != null) {
    plugins_tags.BulmaTagsInput().removeAll();
  }

  if (scripts_tags.BulmaTagsInput != null) {
    scripts_tags.BulmaTagsInput().removeAll();
  }

  BulmaTagsInput.attach(plugins_tags, {
    "source": scripts_data["plugins"]
  });

  BulmaTagsInput.attach(scripts_tags, {
    "source": scripts_data["scripts"]
  })

  plugins_tags.BulmaTagsInput().add(data["plugins"]);
  scripts_tags.BulmaTagsInput().add(data["scripts"]);
}

async function save_config() {
  let text_data = current_editor.getValue();
  let json_data;
  try {
    json_data = JSON.parse(text_data);
  } catch (e) {
    console.log(e)
    let popup_id = create_popup("JSON Invalid!", true);
    setTimeout(function() {remove_popup(popup_id)}, 5000);
    return;
  }

  const url = new URL(window.location.href)
  let selected_machine = url.searchParams.get("m");

  const input_category = document.getElementById("input_category");
  const input_stats_enabled = document.getElementById("input_stats_enabled");
  const plugins_tags = document.getElementById("plugins_tags");
  const scripts_tags = document.getElementById("scripts_tags");

  let packet = {
    "name": selected_machine,
    "new": {
      "category": input_category.value,
      "stats_enabled": input_stats_enabled.checked,
      "plugins": plugins_tags.BulmaTagsInput().items,
      "scripts": scripts_tags.BulmaTagsInput().items,
      "extra_config": json_data
    }
  }

  // Upload JSON data
  try {
    let request = await fetch("/api/machines/update/", {
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": JSON.stringify(packet)
    });

    if (request.status == 200) {
      let popup_id = create_popup("Saved data!");
      setTimeout(function() {remove_popup(popup_id)}, 5000);
    } else {
      let popup_id = create_popup("HTTP" + request.status + ":\n" + await request.text(), true);
      setTimeout(function() {remove_popup(popup_id)}, 10000);
    }
  } catch (e) {
    console.error(e);
  }
}

async function reconnect_machine() {
  const url = new URL(window.location.href)
  let selected_machine = url.searchParams.get("m");

  try {
    let request = await fetch("/api/machines/reconnect/?name="+encodeURIComponent(selected_machine).replace("%20","+")+"&after=15", {
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
    });

    if (request.status == 200) {
      let popup_id = create_popup("Reconnected machine!");
      setTimeout(function() {remove_popup(popup_id)}, 5000);
    } else {
      let popup_id = create_popup("HTTP" + request.status + ":\n" + await request.text(), true);
      setTimeout(function() {remove_popup(popup_id)}, 10000);
    }
  } catch (e) {
    console.error(e);
  }
}

async function pull_config() {
  /*const url = new URL(window.location.href)
  let selected_machine = url.searchParams.get("m");

  let data;
  try {
    let request = await fetch("/api/machines/info/?name="+encodeURIComponent(selected_machine).replace("%20","+"))
    data = await request.json();
  } catch (e) {
    console.error(e);
  }

  let pretty_json = JSON.stringify(data["extra_config"], null, 2);
  current_editor.getModel().setValue(pretty_json);*/

  await edit_machine();
}

async function setup() {
  let data;
  try {
    let request = await fetch("/api/machines/get/all/");
    data = await request.json();
  } catch (e) {
    console.error(e);
  }

  await setup_menu(data);
  await edit_machine();
}

if (document.readyState == "loading") {
  document.addEventListener("DOMContentLoaded", setup);
} else {
  setup();
}

// Also block ctrl + s, and redirect to saving.
document.addEventListener("keydown", async function(e) {
  if (e.key === 's' && e.ctrlKey) {
    e.preventDefault();
    await save_config();
  }
});