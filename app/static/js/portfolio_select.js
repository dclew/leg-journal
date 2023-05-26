function setSelectedPortfolio(portfolioId) {
  // Get the CSRF token from the button data attribute
  const csrfToken = document.querySelector("#portfolioDropdown").dataset.csrf;

  // Store the selected portfolio ID in the session using an AJAX request
  fetch("/set_selected_portfolio", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      portfolioId: portfolioId,
    }),
  })
    .then((response) => response.json())
    .then((data) => console.log(data))
    .catch((error) => console.error(error));
}
