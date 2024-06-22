const register_container = document.getElementById("register-container");

const register = document.getElementById("register");
register.onclick = () => (register_container.style["display"] = "block");

// Login
document
  .getElementById("login-form")
  .addEventListener("submit", async function (event) {
    event.preventDefault(); // Prevent the form from submitting the default way

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const errorMessageDiv = document.getElementById("error-message");

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
      localStorage.setItem("username", data.username);

      // Handle successful login (e.g., display data or redirect to another page)
      console.log("Login successful:", data);
      //   errorMessageDiv.textContent = "Login Successful"; // Clear any previous error message
      document.getElementById("dropbox").style["display"] = "block";
      document.querySelectorAll(".login-container").forEach((el) => {
        el.style.display = "None";
      });
      document.getElementById(
        "greeting"
      ).innerHTML = `Welcome ${data.username}!`;
      fetchFilenames();
    } catch (error) {
      console.error("Error:", error);
      errorMessageDiv.textContent = `Login failed: ${error.message}`;
    }
  });

const register_form = document.getElementById("register-form");

// Register
register_form.addEventListener("submit", async function (event) {
  event.preventDefault(); // Prevent the form from submitting the default way

  const username = document.getElementById("register-username").value;
  const password = document.getElementById("register-password").value;
  const errorMessageDiv = document.getElementById("register-error-message");
  const successMessageDiv = document.getElementById("register-success-message");

  try {
    const response = await fetch("/register", {
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

    // Handle successful registration
    console.log("Registration successful:", data);
    errorMessageDiv.textContent = ""; // Clear any previous error message
    successMessageDiv.textContent = "User registered successfully";
    register_container.style["display"] = "None";
  } catch (error) {
    console.error("Error:", error);
    errorMessageDiv.textContent = `Registration failed: ${error.message}`;
    successMessageDiv.textContent = ""; // Clear success message on error
  }
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
  let username = localStorage.getItem("username");

  fetch(`/upload/${username}`, {
    method: "POST",
    body: formData,
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
  let username = localStorage.getItem("username");
  fetch(`/files/${username}`)
    .then((response) => response.json())
    .then((data) => {
      console.log(data);

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
                <a href="/user/${username}/files/${file.filename}" target="_blank">Download</a>
                <a onclick="deleteFile('${file.filename}')">Delete</a>
                <a onclick="createLink('${file.id}')">Create Link</a>
            </td>
        `;
        fileTableBody.appendChild(row);
      });
    })
    .catch((error) => console.error("Error:", error));
}

// Delete file from server
function deleteFile(fileId) {
  // console.log(fileId);
  let username = localStorage.getItem("username");
  fetch(`/user/${username}/files/${fileId}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      fetchFilenames(); // Refresh the file list after deletion
    })
    .catch((error) => console.error("Error:", error));
}

function createLink(file_id) {
  fetch(`/generateLink/${file_id}`, {
    method: "POST",
  })
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
      navigator.clipboard.writeText(data.link);
    })
    .catch((error) => console.error("error: ", error));
}
