document.addEventListener("DOMContentLoaded", function() {
    let selectedImages = new Set();

    // Image selection handling
    document.querySelectorAll(".game-image").forEach(img => {
        img.addEventListener("click", function() {
            let filename = img.getAttribute("data-filename");
            if (selectedImages.has(filename)) {
                selectedImages.delete(filename);
                img.classList.remove("selected");
            } else {
                selectedImages.add(filename);
                img.classList.add("selected");
            }
        });
    });

    // Send the answer to the server
    document.getElementById("submit-btn").addEventListener("click", function() {
        fetch("/check_room1_answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ selected_images: Array.from(selectedImages) })
        })
        .then(response => response.json())
        .then(data => {
            let message = document.getElementById("result-message");
            message.textContent = data.message;
            message.style.color = data.status === "success" ? "green" : "red";

            if (data.status === "success") {
                // Display the button for the next room + the explosion image
                const nextBtn = document.getElementById("next-room-btn");
                const boomImg = document.getElementById("kremlin-boom");
                if (nextBtn) nextBtn.style.display = "block";
                if (boomImg) {
                    boomImg.style.display = "block";
                    // Optional: smooth scrolling to the image and the button
                    boomImg.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }
        })
        .catch(error => console.error("שגיאה:", error));
    });
});
