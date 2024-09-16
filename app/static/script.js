function showRegister() {
  document.getElementById("register-container").style["display"] = "block";
}

function hideRegister() {
  document.getElementById("register-container").style["display"] = "None";
}

document
  .getElementById("login-form")
  .addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent the form from submitting the default way

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }
      const data = await response.json();

      localStorage.setItem("apikey", data.apikey);

      // Handle successful login (e.g., display data or redirect to another page)
      document.getElementById("dropbox").style["display"] = "block";
      document.querySelectorAll(".login-container").forEach((el) => {
        el.style.display = "None";
      });
      document.getElementById(
        "greeting"
      ).innerHTML = `Welcome ${data.username}!`;

      // TODO need some fix here for how fetchFolderNames gets called
      fetchFolderNames(data.folderId);
    } catch (error) {
      alertify.error(`Login failed: ${error.message}`);
    }
  });

// Register
document
  .getElementById("register-form")
  .addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent the form from submitting the default way

    const username = document.getElementById("register-username").value;
    const password = document.getElementById("register-password").value;

    fetch("/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    }).then((response) => {
      if (response.status !== 200) {
        alertify.error("Registration failed: User already exists");
      } else {
        alertify.success("User registered successfully");
        hideRegister();
      }
    });
  });

const dropZone = document.getElementById("dropZone");

const fileTableBody = document.querySelector("#fileList tbody");

// Prevent default behavior for drag-and-drop events
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, preventDefaults, false);
  document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

// Highlight drop zone when file is dragged over
["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(
    eventName,
    () => {
      dropZone.classList.add("highlight");
    },
    false
  );
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(
    eventName,
    () => {
      dropZone.classList.remove("highlight");
    },
    false
  );
});

// Handle dropped files
dropZone.addEventListener("drop", handleDrop, false);

function handleDrop(e) {
  let dt = e.dataTransfer;
  let files = dt.files;

  handleFiles(files);
}

// Handle uploaded files
function handleFiles(files) {
  [...files].forEach(uploadFile);
}

// Upload file to server
function uploadFile(file) {
  const currentDir = localStorage.getItem("currentDir");

  let formData = new FormData();
  formData.append("file", file);

  fetch(`/upload/${currentDir}`, {
    method: "POST",
    body: formData,
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then(() => {
      fetchFolderNames(currentDir);
    })
    .catch((error) => console.error("Error:", error));
}

async function downloadFile(file_id) {
  const response = await fetch(`/user/files/${file_id}`, {
    method: "GET",
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  }).catch((error) => console.error("Error:", error));

  const disposition = response.headers.get("Content-Disposition");
  const filename = disposition.match(/filename="?([^"]*)"?/)[1];

  // Create a Blob from the response
  const blob = await response.blob();

  // Create a link element, set the download attribute and click it
  const link = document.createElement("a");
  const objectURL = URL.createObjectURL(blob);
  link.href = objectURL;
  link.download = filename; // Set the filename here
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(objectURL); // Clean up
}

// Delete file from server
function deleteFile(fileId) {
  const currentDir = localStorage.getItem("currentDir");
  fetch(`/user/files/remove/${fileId}`, {
    method: "DELETE",
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then(() => {
      fetchFolderNames(currentDir); // Refresh the file list after deletion
    })
    .catch((error) => console.error("Error:", error));
}

function createLink(file_id) {
  fetch(`/user/files/link/${file_id}`, {
    method: "POST",
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      copyText(data.link);
    })
    .catch((error) => console.error("error: ", error));
}

// API Key functions
const apiButton = document.getElementById("api-key");
apiButton.addEventListener("click", async () => {
  fetch("/generate-api-key", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const apiTable = `
      <table border="1" style="width: 100%; text-align: left;">
       <thead>
       </thead>
       <tbody>
        <tr>
        <td>${data}</td>
        <td><button onclick='copyText("${data}")'>Copy</button></td>
        </tr>
        `;

      alertify.alert(
        "Copy API key below, this will not be shown again",
        apiTable
      );
    });
});

function copyText(text) {
  navigator.clipboard.writeText(text);
  alertify.success("Link copied to clipboard!");
}

// Manage api keys
async function manageAPIKeys() {
  // Create programmatic alerts
  let apiTableHTML = `
                <table border="1" style="width: 100%; text-align: left;">
                    <thead>
                      <tr>
                        <th>Key</th>
                        <th>Remove?</th>
                      </tr>
                    </thead>
                    <tbody>
  `;

  data = await fetch("/get-api-key", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      data.keys.forEach((key) => {
        apiTableHTML += `
    <tr>
      <td>${key.key}</td>
      <td><button onclick="removeKey(${key.id})">Remove</button>
    </tr>
    `;
      });
      apiTableHTML += `
           </tbody>
                </table>`;

      alertify.alert("table", apiTableHTML).set({ title: "API Keys" });
    });
}

const apiManage = document.getElementById("api-manage");
apiManage.addEventListener("click", async () => {
  manageAPIKeys();
});

function removeKey(id) {
  fetch(`/delete-api-key/${id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      manageAPIKeys();
    });
}
