// API Key functions
// Manage api keys
async function generateAPIKeys() {
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
}

async function manageAPIKeys() {
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
