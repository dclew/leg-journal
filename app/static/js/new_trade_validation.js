function validateForm() {
  // Get all the input values
  var symbolInput = document.getElementById("symbol-input");
  var quantityInput = document.getElementById("quantity-input");
  var priceInput = document.getElementById("price-input");
  var strikePriceInput = document.getElementById("strike-price-input");

  // Reset all error messages and field styles
  var errorMessages = document.getElementsByClassName("error-message");
  for (var i = 0; i < errorMessages.length; i++) {
    errorMessages[i].innerText = "";
  }
  symbolInput.classList.remove("is-invalid");
  quantityInput.classList.remove("is-invalid");
  priceInput.classList.remove("is-invalid");
  strikePriceInput.classList.remove("is-invalid");

  var isValid = true;

  // Validate the symbol input
  var symbolRegex = /^[A-Z]+$/;
  if (!symbolRegex.test(symbolInput.value)) {
    document.getElementById("symbol-error").innerText =
      "Please enter uppercase letters for the symbol.";
    symbolInput.classList.add("is-invalid");
    isValid = false;
  }

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

  // Validate the strike price input
  if (
    isNaN(strikePriceInput.value) ||
    parseFloat(strikePriceInput.value) <= 0
  ) {
    document.getElementById("strike-price-error").innerText =
      "Please enter a valid positive number for the strike price.";
    strikePriceInput.classList.add("is-invalid");
    isValid = false;
  }

  return isValid;
}
