function createFolder() {
  let filePath = document.getElementById("filePath");
  let current_dir = filePath.innerHTML;
  alertify
    .prompt("Enter folder name", "new_folder", function (evt, new_dir) {
      // I dont want to augment the display unless moving into a file
      // filePath.innerHTML += "/" + new_dir;
      // Call fetchFiles from here
      fetch("/add_folder", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          access_token: localStorage.getItem("apikey"),
        },
        body: JSON.stringify({ current_dir, new_dir }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);
          fetchFolderNames(current_dir);
        });
    })
    .set({ title: "New Folder" });
}

// Fetch filenames from server
function fetchFilenames(id) {
  fetch(`/files`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      access_token: localStorage.getItem("apikey"),
    },
    body: JSON.stringify({ id }),
  })
    .then((response) => response.json())
    .then((data) => {
      // fileTableBody.innerHTML = ""; // Clear the current list
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
            <td>${file.name}</td>
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

function fetchFolderNames(id) {
  if (typeof id === "undefined") {
    id = null;
  }
  console.log(id)
  console.log(typeof id)
  fetch("/folders", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      access_token: localStorage.getItem("apikey"),
    },
    body: JSON.stringify({ id }),
  })
    .then((response) => response.json())
    .then((data) => {
      fileTableBody.innerHTML = ""; // Clear the current list
      data.folders.forEach((folder) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>
          <a onclick="fetchFolderNames('${folder.name}')">${folder.name}</a>
            <img src="folder.png" height="20px" alt="folderImg"></td>
          <td> ~ </td>
          <td> ~ </td>
          <td>
              <a onclick="deleteFolder('${folder.id}')">Delete</a>
          </td>
      `;
        fileTableBody.appendChild(row);
      });
      fetchFilenames(data.current_folder);
      localStorage.setItem("currentDir", data.current_folder);
    })
    .catch((error) => console.error("Error:", error));
}
