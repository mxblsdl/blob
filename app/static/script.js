const register_container = document.getElementById("register-container");

const register = document.getElementById("register");
register.onclick = () => (register_container.style["display"] = "block");

// TODO refactor for consistency?
// Login
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
      fetchFilenames();
    } catch (error) {
      alertify.error(`Login failed: ${error.message}`);
    }
  });

const register_form = document.getElementById("register-form");

// Register
register_form.addEventListener("submit", async function (event) {
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
      register_container.style["display"] = "None";
    }
  });
});

const dropZone = document.getElementById("dropZone");
// const fileList = document.getElementById("fileList");
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
  let formData = new FormData();
  formData.append("file", file);

  fetch(`/upload`, {
    method: "POST",
    body: formData,
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      fetchFilenames();
    })
    .catch((error) => console.error("Error:", error));
}

// Fetch filenames from server
function fetchFilenames() {
  fetch(`/files`, {
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      fileTableBody.innerHTML = ""; // Clear the current list
      data.files.forEach((file) => {
        if ((file.size > 1000) & (file.size < 9999)) {
          size = (file.size / 1000).toFixed(1) + " kb";
        } else if ((file.size > 9999) & (file.size < 9999999)) {
          size = (file.size / 1000000).toFixed(1) + " Mb";
        } else {
          size = file.size + " bytes";
        }

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${file.filename}</td>
            <td>${size}</td>
            <td>${file.created_at}</td>
            <td>
                <a onclick="downloadFile('${file.id}')">Download</a>
                <a onclick="deleteFile('${file.id}')">Delete</a>
                <a onclick="createLink('${file.id}')">Create Link</a>
            </td>
        `;
        fileTableBody.appendChild(row);
      });
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
  fetch(`/user/files/remove/${fileId}`, {
    method: "DELETE",
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then(() => {
      fetchFilenames(); // Refresh the file list after deletion
    })
    .catch((error) => console.error("Error:", error));
}

function createLink(file_id) {
  fetch(`/generateLink/${file_id}`, {
    method: "POST",
    headers: {
      access_token: localStorage.getItem("apikey"),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      alertify.success("Link copied to clipboard!");
      navigator.clipboard.writeText(data.link);
    })
    .catch((error) => console.error("error: ", error));
}
