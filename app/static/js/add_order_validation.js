function validateForm() {
  // Get all the input values
  var quantityInput = document.getElementById("quantity-input");
  var priceInput = document.getElementById("price-input");

  // Reset all error messages and field styles
  var errorMessages = document.getElementsByClassName("error-message");
  for (var i = 0; i < errorMessages.length; i++) {
    errorMessages[i].innerText = "";
  }
  quantityInput.classList.remove("is-invalid");
  priceInput.classList.remove("is-invalid");

  var isValid = true;

  // Validate the quantity input
  if (isNaN(quantityInput.value) || parseFloat(quantityInput.value) <= 0) {
    document.getElementById("quantity-error").innerText =
      "Please enter a valid positive number for the quantity.";
    quantityInput.classList.add("is-invalid");
    isValid = false;
  }

  // Validate the price input
  if (isNaN(priceInput.value) || parseFloat(priceInput.value) <= 0) {
    document.getElementById("price-error").innerText =
      "Please enter a valid positive number for the price.";
    priceInput.classList.add("is-invalid");
    isValid = false;
  }

  return isValid;
}
