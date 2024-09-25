function showRegister() {
  document.getElementById("register-container").style["display"] = "block";
}

function hideRegister() {
  document.getElementById("register-container").style["display"] = "None";
}

async function login(event) {
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
    document.getElementById("greeting").innerHTML = `Welcome ${data.username}!`;

    fetchFolderNames(data.folderId);
  } catch (error) {
    alertify.error(`Login failed: ${error.message}`);
  }
}

// Register
async function register(event) {
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
}
