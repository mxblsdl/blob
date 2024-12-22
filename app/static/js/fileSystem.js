function createFolder() {
  const currentDir = localStorage.getItem("currentDir");
  alertify
    .prompt("Enter folder name", "new_folder", function (evt, newDir) {
      fetch("/add_folder", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          access_token: localStorage.getItem("apikey"),
        },
        body: JSON.stringify({ currentDir, newDir }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log(data);
          fetchFolderNames(currentDir);
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
          <a onclick="fetchFolderNames('${folder.id}')">${folder.name}</a>
            <img src="folder.png" height="20px" alt="folderImg"></td>
          <td> ~ </td>
          <td> ~ </td>
      `;
        if (folder.name != "../") {
          row.innerHTML += `<td>
              <a onclick="deleteFolder('${folder.id}')">Delete</a>
          </td>`;
        }

        fileTableBody.appendChild(row);
      });
      fetchFilenames(data.current_folder);
      createFilePath(data.current_folder);
      localStorage.setItem("currentDir", data.current_folder);
    })
    .catch((error) => console.error("Error:", error));
}

// function createFilePath(id) {
//   fetch(`/filepath/${id}`, {
//     method: "GET",
//     headers: {
//       access_token: localStorage.getItem("apikey"),
//     },
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       document.getElementById("filePath").innerHTML = data;
//     });
// }
