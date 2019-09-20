var port = browser.extension
  .getBackgroundPage()
  .browser.runtime.connectNative("com.elevenpaths.easydoh");

document.getElementById("change-content").onclick = function() {
  buttonAction();
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
});

port.onDisconnect.addListener(response => {
  console.log("Disconnect: " + response);
  document.getElementById("popup-content").classList.add("hidden");
  document.getElementById("error-content").classList.remove("hidden");
});

function buttonAction() {
  var mode = document.getElementById("mode-select");
  var value_mode = mode.options[mode.selectedIndex].value;
  var uri = document.getElementById("list-select");
  var value_uri = uri.options[uri.selectedIndex].value;
  var data = { mode: value_mode, uri: value_uri };
  port.postMessage(JSON.stringify(data));
  document.getElementById("reboot").classList.remove("hidden");
  document.getElementById("popup-content").classList.add("hidden");
}
