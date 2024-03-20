function format(_format) {
  var args = Array.prototype.slice.call(arguments, 1);
  return _format.replace(/{(\d+)}/g, function(match, number) { 
    return typeof args[number] != 'undefined'
      ? args[number] 
      : match
    ;
  });
};

function make_id(length) {
  let result = '';
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (var i=0; i<length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
}

function create_popup(reason, is_danger) {
  // Create the div
  const div = document.createElement("div");

  // Create a custom ID for removing only the targetted popup.
  var id = make_id(10);
  div.id = id;

  div.style.position = "fixed";
  div.style.top =    "25px";
  div.style.right =  "40%";
  div.style.width =  "20%";
  div.style.zIndex = "100";

  const notification = document.createElement("div")
  notification.classList.add("notification");
  if (!is_danger) {
    notification.classList.add("is-primary");
  } else {
    notification.classList.add("is-danger");
  }
  // Add a header to the div
  const text_node = document.createTextNode(reason);
  // Add the close button
  const button = document.createElement("button");
  button.classList.add("delete")
  button.onclick = function() { remove_popup(id,reason) };
  // Put everything together
  notification.appendChild(button);
  notification.appendChild(text_node)
  div.appendChild(notification);
  // Add it to the HTML page.
  const body = document.body;
  body.appendChild(div);
}

function remove_popup(popup,reason) {
  var elem = document.getElementById(popup)
  elem.parentNode.removeChild(elem);
}