$(function() {
  var data = { mode: "init", uri: "" };
  port.postMessage(JSON.stringify(data));

  loadJSON();
});

var port = browser.extension
  .getBackgroundPage()
  .browser.runtime.connectNative("com.elevenpaths.easydoh");

var dnsValues = "";

document.getElementById("change-content").onclick = function() {
  buttonAction();
};

document.getElementById("reset").onclick = function() {
  buttonReset();
};

document.getElementById("serverManualInput").onkeyup = function() {
  validateURL = validator.isURL(
    document.getElementById("serverManualInput").value
  );

  if (validateURL) {
    document.getElementById("change-content").removeAttribute("disabled");
  } else {
    document.getElementById("change-content").setAttribute("disabled", true);
  }
};

document.getElementById("serverInput").onclick = function() {
  var server = document.getElementById("serverInput");
  var serverSelect = server.options[server.selectedIndex].value;

  if (serverSelect === "manual") {
    document.getElementById("serverManualInput").classList.remove("d-none");
    document.getElementById("change-content").setAttribute("disabled", true);
  } else {
    document.getElementById("serverManualInput").classList.add("d-none");
    document.getElementById("serverManualInput").value = "";
    document.getElementById("change-content").removeAttribute("disabled");
  }
};

// Disconnect port on unload
window.addEventListener("unload", function() {
  port.disconnect();
});

/*
Listen for messages from the app.
*/
port.onMessage.addListener(response => {
  console.log("Received: " + response);
  mode = response["mode"];
  uri = getDnsFromUri(response["uri"]);

  loadJSON(mode, uri);
});

port.onDisconnect.addListener(response => {
  console.log("Disconnect: " + response);

  message =
    '<p>Addon not detected.</p><p>Check if it is in the right path or download and install it from <a href="https://easydoh.e-paths.com/download.html">here</a>.</p>';
  setMessage(message);
});

function buttonAction() {
  var mode = document.getElementById("modeInput");
  var valueMode = mode.options[mode.selectedIndex].value;
  var uri = document.getElementById("serverInput");
  var valueUri = uri.options[uri.selectedIndex].value;

  if (valueUri === "manual") {
    valueUri = "manual;" + document.getElementById("serverManualInput").value;
  } else {
    valueUri = dnsValues[valueUri].url;
  }

  sendData(valueMode, valueUri);
}

function buttonReset() {
  var valueMode = 1;
  var valueUri = dnsValues["default"].url;

  sendData(valueMode, valueUri);
}

function getDnsFromUri(uri) {
  var val = "manual;" + uri;
  for (value in dnsValues) {
    if (dnsValues[value]["url"] == uri) {
      val = value;
      break;
    }
  }
  return val;
}

function sendData(mode, uri) {
  var data = { mode: mode, uri: uri };
  port.postMessage(JSON.stringify(data));

  message =
    "<p>Restart the browser to apply changes<br/>EasyDoH will show Cloudfare configuration by default,<br/>but your configuration wil be shown in TRR <i>about:config</i></p>";
  setMessage(message);
}

function setMessage(message) {
  document.getElementById("popup-content").classList.add("d-none");

  messages = document.getElementById("messages");
  messages.innerHTML = message;
  messages.classList.remove("d-none");
}

function setOptionsValue(mode, uri) {
  document.getElementById("modeInput").options.selectedIndex = mode;
  var serverInput = document.getElementById("serverInput").options;

  if (uri === "default") {
    uri = "cloudflare";
  } else if (uri.includes("manual;")) {
    var manual = uri.split(";");
    document.getElementById("serverManualInput").value = manual[1];
    document.getElementById("serverManualInput").classList.remove("d-none");
    document.getElementById("change-content").setAttribute("disabled", true);
    uri = manual[0];
  }

  for (var i = 0; i < serverInput.length; i++) {
    if (uri == serverInput[i].value) {
      serverInput.selectedIndex = i;
      break;
    }
  }
}

function loadJSON(mode, uri) {
  xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      txt = "";
      dnsValues = JSON.parse(this.responseText);

      txt += '<option value="manual">Insert custom DoH server...</option>';
      for (x in dnsValues) {
        if (x != "default") {
          txt += '<option value="' + x + '">' + dnsValues[x].name + "</option>";
        }
      }
      document.getElementById("serverInput").innerHTML = txt;

      setOptionsValue(mode, uri);
    }
  };
  xmlhttp.open("GET", "doh.json", true);
  xmlhttp.send();
}
