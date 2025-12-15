document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Create activity name heading
        const nameHeading = document.createElement("h4");
        nameHeading.textContent = name;
        activityCard.appendChild(nameHeading);

        // Create description paragraph
        const descriptionP = document.createElement("p");
        descriptionP.textContent = details.description;
        activityCard.appendChild(descriptionP);

        // Create schedule paragraph
        const scheduleP = document.createElement("p");
        const scheduleStrong = document.createElement("strong");
        scheduleStrong.textContent = "Schedule:";
        scheduleP.appendChild(scheduleStrong);
        scheduleP.appendChild(document.createTextNode(" " + details.schedule));
        activityCard.appendChild(scheduleP);

        // Create availability paragraph
        const availabilityP = document.createElement("p");
        const availabilityStrong = document.createElement("strong");
        availabilityStrong.textContent = "Availability:";
        availabilityP.appendChild(availabilityStrong);
        availabilityP.appendChild(document.createTextNode(" " + spotsLeft + " spots left"));
        activityCard.appendChild(availabilityP);

        // Create participants section
        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";

        const participantsLabel = document.createElement("p");
        const participantsStrong = document.createElement("strong");
        participantsStrong.textContent = "Participants:";
        participantsLabel.appendChild(participantsStrong);
        participantsSection.appendChild(participantsLabel);

        if (details.participants.length > 0) {
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";

          details.participants.forEach(email => {
            const li = document.createElement("li");

            const emailSpan = document.createElement("span");
            emailSpan.className = "participant-email";
            emailSpan.textContent = email;
            li.appendChild(emailSpan);

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-btn";
            deleteBtn.dataset.activity = name;
            deleteBtn.dataset.email = email;
            deleteBtn.title = "Unregister participant";
            deleteBtn.setAttribute("aria-label", "Unregister participant");
            deleteBtn.textContent = "🗑️";
            deleteBtn.addEventListener('click', handleUnregister);
            li.appendChild(deleteBtn);

            participantsList.appendChild(li);
          });

          participantsSection.appendChild(participantsList);
        } else {
          const noParticipantsP = document.createElement("p");
          noParticipantsP.className = "no-participants";
          noParticipantsP.textContent = "No participants yet";
          participantsSection.appendChild(noParticipantsP);
        }

        activityCard.appendChild(participantsSection);
        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle participant unregistration
  async function handleUnregister(event) {
    const button = event.target;
    const activityName = button.dataset.activity;
    const email = button.dataset.email;

    if (!confirm(`Are you sure you want to unregister ${email} from ${activityName}?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activityName)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        // Refresh the activities list
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "Failed to unregister";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh the activities list
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
