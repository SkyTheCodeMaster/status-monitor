async function load_db_counts() {
  let data;
  try {
    let request = await fetch("/api/srv/get/");
    data = await request.json();
  } catch (e) {
    console.error(e)
  }
  const connected_machines = document.getElementById("connected_machines");
  connected_machines.innerText = format(connected_machines.innerText, data["online_machines"], data["total_machines"]);
}

async function setup() {
  await load_db_counts();
}

if (document.readyState == "loading") {
  document.addEventListener("DOMContentLoaded", setup);
} else {
  setup();
}