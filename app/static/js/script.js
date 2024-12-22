// Upload files
// const dropZone = document.getElementById("dropZone");

// const fileTableBody = document.querySelector("#fileList tbody");

// Prevent default behavior for drag-and-drop events
// ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
//   dropZone.addEventListener(eventName, preventDefaults, false);
//   document.body.addEventListener(eventName, preventDefaults, false);
// });

// function preventDefaults(e) {
//   e.preventDefault();
//   e.stopPropagation();
// }

// Highlight drop zone when file is dragged over


// Handle dropped files
// dropZone.addEventListener("drop", handleDrop, false);

// function handleDrop(e) {
//   let dt = e.dataTransfer;
//   let files = dt.files;

//   handleFiles(files);
// }

// // Handle uploaded files
// function handleFiles(files) {
//   [...files].forEach(uploadFile);
// }

// Upload file to server
// function uploadFile(file) {
//   const currentDir = localStorage.getItem("currentDir");

//   let formData = new FormData();
//   formData.append("file", file);

//   fetch(`/upload/${currentDir}`, {
//     method: "POST",
//     body: formData,
//     headers: {
//       access_token: localStorage.getItem("apikey"),
//     },
//   })
//     .then((response) => response.json())
//     .then(() => {
//       fetchFolderNames(currentDir);
//     })
//     .catch((error) => console.error("Error:", error));
// }

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

function copyText(text) {
  navigator.clipboard.writeText(text);
  alertify.success("Link copied to clipboard!");
}
