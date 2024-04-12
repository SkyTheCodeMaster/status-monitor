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
  return div.id;
}

function remove_popup(popup,reason) {
  var elem = document.getElementById(popup)
  elem.parentNode.removeChild(elem);
}

function format_human(human, decimals = 2) {
  if (+human < 1000) return human;
  if (!+human) return '0';

  const k = 1000;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['', 'k', 'M', 'B', 'T', 'Qd', 'Qt', 'Sx', 'Sp', 'Oc', 'No', 'De', 'Ud', 'Du'];

  const i = Math.floor(Math.log(human) / Math.log(k));

  return `${parseFloat((human / Math.pow(k, i)).toFixed(dm))}${sizes[i]}`;
}

function format_bytes(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function format_bytes_per_second(bytes, decimals = 2) {;
  if (!+bytes) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B/s', 'Kbps', 'Mbps', 'Gbps', 'Tbps', 'Pbps', 'Ebps', 'Zbps', 'Ybps'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function format_hashes_per_second(bytes, decimals = 2) {
  if (!+bytes) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['H/s', 'KH/s', 'MH/s', 'GH/s', 'TH/s', 'PH/s', 'EH/s', 'ZH/s', 'YH/s'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function to_title_case(str) {
  return str.replace(
    /\w\S*/g,
    function(txt) {
      return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    }
  );
}

function _longdiv(numerator, denominator) {
  let remainder = numerator % denominator;
  let quotient = ((numerator-remainder)/denominator);

  return [quotient, remainder];
}

function parse_seconds(_seconds, decimal_length = 0) {
  // Turn seconds into year month day hour minute second, like
  // 1y 3m 2d 16h 13m 45s
  
  let [_minutes, seconds]  = _longdiv(_seconds, 60);
  let [_hours, minutes] = _longdiv(_minutes, 60);
  let [_days, hours] = _longdiv(_hours, 60);
  let [_months, days] = _longdiv(_days, 24);
  let [_years, months] = _longdiv(_months, 30);
  let years = Math.floor(_years/12);

  let out = ""

  if (years != 0) {
    out = out + format("{0}y ", years.toFixed(decimal_length))
  }
  if (months != 0) {
    out = out + format("{0}m ", months.toFixed(decimal_length))
  }
  if (days != 0) {
    out = out + format("{0}d ", days.toFixed(decimal_length))
  }
  if (hours != 0) {
    out = out + format("{0}h ", hours.toFixed(decimal_length))
  }
  if (minutes != 0) {
    out = out + format("{0}m ", minutes.toFixed(decimal_length))
  }
  if (seconds != 0) {
    out = out + format("{0}s ", seconds.toFixed(decimal_length))
  }

  return out
}