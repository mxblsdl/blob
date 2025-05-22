htmx.find("#dropZone").addEventListener("drop", async (e) => {
    const files = e.dataTransfer.files;
    const folder = htmx.find("#folderId").value;
    const apiKey = htmx.find("#key").value;

    const uploadPromises = Array.from(files).map(async (file) => {
      const formData = new FormData();
      // Add the file to FormData
      formData.append("file", file);
      formData.append("folder_id", folder);

      // Form data needs a JS method to attach the data
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
        headers: {
          access_token: apiKey,
        },
      });
      if (!response.ok) {
        console.error(`Error uploading ${file.name}`, error);
      }
    });
    try {
      await Promise.all(uploadPromises);
      // triggers the update
      htmx.trigger("#fileTable", "triggerItems");
      alertify.success("File Upload Successful");
    } catch (error) {
      alertify.error("Upload Failed");
    }
  });

  // Adds api key header to all requests
  document.body.addEventListener("htmx:configRequest", (e) => {
    const apiKey = htmx.find("#key").getAttribute("value");
    e.detail.headers["access_token"] = apiKey;
  });