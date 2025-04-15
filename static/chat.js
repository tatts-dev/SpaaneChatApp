let socket = io();
let room = "";
let username = "";

function joinRoom() {
  username = document.getElementById("username").value;
  room = document.getElementById("room").value;

  socket.emit("join", { username, room });
  document.getElementById("chat").style.display = "block";
}

socket.on("message", (data) => {
  const msgBox = document.getElementById("messages");
  const p = document.createElement("p");
  p.innerText = `${data.username}: ${data.msg}`;
  msgBox.appendChild(p);
});

function sendMessage() {
  const msg = document.getElementById("message").value;
  socket.emit("send_message", { username, msg, room });
  document.getElementById("message").value = "";
}
